import json
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
from ollama import AsyncClient, ResponseError
from py_agent_core.backends.base import BaseBackend, BackendChunk, ToolCallChunk

logger = logging.getLogger(__name__)

class OllamaBackend(BaseBackend):
    """Adapter for local Ollama service instances."""
    
    _unsupported_reasoning_models = set()

    def __init__(
        self,
        client: Optional[AsyncClient] = None,
        model: str = "llama3",
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        supports_reasoning: Optional[bool] = None,
    ):
        """
        Args:
            client: Optional Ollama AsyncClient instance. Constructs a default one if None.
            model: The name of the model to use.
            temperature: Default temperature.
            top_p: Default top_p.
            supports_reasoning: Explicit override for reasoning capability.
        """
        super().__init__(temperature=temperature, top_p=top_p)
        self.client = client or AsyncClient()
        self.model = model
        self._supports_reasoning_override = supports_reasoning

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[BackendChunk, None]:
        # Ollama SDK expects tool call arguments to be pre-parsed dictionaries rather than JSON strings
        formatted_messages = []
        for msg in messages:
            new_msg = dict(msg)
            # Sanitize thinking traces from message history before requesting completion
            if "thinking" in new_msg:
                del new_msg["thinking"]
                
            if "tool_calls" in new_msg and new_msg["tool_calls"]:
                formatted_tool_calls = []
                for tc in new_msg["tool_calls"]:
                    new_tc = dict(tc)
                    if "function" in new_tc:
                        new_func = dict(new_tc["function"])
                        args = new_func.get("arguments")
                        if isinstance(args, str):
                            try:
                                parsed = json.loads(args)
                                if isinstance(parsed, dict):
                                    new_func["arguments"] = parsed
                                else:
                                    new_func["arguments"] = {"invalid_arguments": args}
                            except json.JSONDecodeError:
                                new_func["arguments"] = {"invalid_arguments": args}
                        elif not isinstance(args, dict):
                            new_func["arguments"] = {"invalid_arguments": str(args)}
                        new_tc["function"] = new_func
                    formatted_tool_calls.append(new_tc)
                new_msg["tool_calls"] = formatted_tool_calls
            formatted_messages.append(new_msg)

        kwargs = {}
        if tools:
            kwargs["tools"] = tools

        options_dict = {}
        if self.temperature is not None:
            options_dict["temperature"] = self.temperature
        if self.top_p is not None:
            options_dict["top_p"] = self.top_p
        if options_dict:
            kwargs["options"] = options_dict

        # Determine reasoning capability
        use_reasoning = False
        thinking_level = "off"
        if options and "thinking_level" in options:
            thinking_level = options["thinking_level"]
            if thinking_level != "off":
                if self._supports_reasoning_override is not False:
                    if self._supports_reasoning_override is True or self.model not in self._unsupported_reasoning_models:
                        kwargs["think"] = True
                        use_reasoning = True
            else:
                kwargs["think"] = False

        # Retry loop to dynamically fallback when the think parameter is unsupported
        while True:
            try:
                response_stream = await self.client.chat(
                    model=self.model,
                    messages=formatted_messages,
                    stream=True,
                    **kwargs
                )
                break
            except ResponseError as e:
                err_msg = str(e)
                if use_reasoning and ("think" in err_msg or "parameter" in err_msg or getattr(e, "status_code", None) == 400):
                    self._unsupported_reasoning_models.add(self.model)
                    logger.warning(
                        "Thinking level '%s' enabled for model '%s', but the model or Ollama server does not support the 'think' option. "
                        "Gracefully falling back to execution without it.",
                        thinking_level, self.model
                    )
                    kwargs.pop("think", None)
                    use_reasoning = False
                    continue
                else:
                    raise
        
        tool_call_ids = []
        yielded_arguments = {}

        try:
            async for chunk in response_stream:
                message = chunk.get("message", {})
                text_delta = message.get("content", "")
                thinking_delta = message.get("thinking", "")
                
                tool_calls = None
                raw_tool_calls = message.get("tool_calls")
                if raw_tool_calls:
                    tool_calls = []
                    for idx, tc in enumerate(raw_tool_calls):
                        func = tc.get("function", {})
                        
                        # Track tool calls by ID (or sequence position) to assign stable indices
                        tc_id = tc.get("id")
                        if not tc_id:
                            tc_id = f"fallback_{idx}_{func.get('name')}"
                            
                        if tc_id not in tool_call_ids:
                            tool_call_ids.append(tc_id)
                        stable_idx = tool_call_ids.index(tc_id)
                        
                        args = func.get("arguments", "")
                        if not isinstance(args, str):
                            args = json.dumps(args)
                        
                        # Calculate the delta of the arguments string compared to what we've already yielded
                        # for this specific tool call, preventing double-concatenation.
                        previous_args = yielded_arguments.get(tc_id, "")
                        if args.startswith(previous_args):
                            args_delta = args[len(previous_args):]
                        else:
                            args_delta = args
                        yielded_arguments[tc_id] = args
                        
                        tool_calls.append(ToolCallChunk(
                            index=stable_idx,
                            id=tc_id,
                            name=func.get("name"),
                            arguments=args_delta
                        ))
                        
                yield BackendChunk(
                    text=text_delta or None,
                    thinking=thinking_delta or None,
                    tool_calls=tool_calls
                )
        except GeneratorExit:
            # Gracefully handle preemption to prevent asyncio generator cleanup warnings
            return
        finally:
            try:
                await response_stream.aclose()
            except RuntimeError as e:
                # Suppress the known internal contextlib / async generator race condition inside the ollama SDK
                if "asynchronous generator is already running" not in str(e):
                    raise
