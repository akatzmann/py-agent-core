import json
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
from ollama import AsyncClient
from py_agent_core.backends.base import BaseBackend, BackendChunk, ToolCallChunk

logger = logging.getLogger(__name__)

class OllamaBackend(BaseBackend):
    """Adapter for local Ollama service instances."""
    
    def __init__(self, client: Optional[AsyncClient] = None, model: str = "llama3"):
        """
        Args:
            client: Optional Ollama AsyncClient instance. Constructs a default one if None.
            model: The name of the model to use.
        """
        self.client = client or AsyncClient()
        self.model = model

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

        if options and "thinking_level" in options:
            thinking_level = options["thinking_level"]
            if thinking_level != "off":
                kwargs["think"] = True
                model_lower = self.model.lower()
                if not any(k in model_lower for k in ("r1", "think", "reasoning", "cot")):
                    logger.warning(
                        "Thinking level '%s' enabled for model '%s', but the model may not natively support reasoning. "
                        "Only models specifically trained for chain-of-thought (e.g. deepseek-r1) support thinking options.",
                        thinking_level, self.model
                    )
            else:
                kwargs["think"] = False

        response_stream = await self.client.chat(
            model=self.model,
            messages=formatted_messages,
            stream=True,
            **kwargs
        )
        
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
                        args = func.get("arguments", "")
                        if not isinstance(args, str):
                            args = json.dumps(args)
                        
                        tool_calls.append(ToolCallChunk(
                            index=idx,
                            id=tc.get("id"),
                            name=func.get("name"),
                            arguments=args
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
