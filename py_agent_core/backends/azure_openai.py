import logging
import openai
from typing import AsyncGenerator, List, Dict, Any, Optional
from openai import AsyncAzureOpenAI
from py_agent_core.backends.base import BaseBackend, BackendChunk, ToolCallChunk

logger = logging.getLogger(__name__)

class AzureOpenAIBackend(BaseBackend):
    """Adapter for Microsoft Azure OpenAI Service."""
    
    _unsupported_reasoning_models = set()
    _unsupported_sampling_models = set()

    def __init__(
        self,
        client: AsyncAzureOpenAI,
        model: str,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        supports_reasoning: Optional[bool] = None,
        supports_sampling: Optional[bool] = None,
    ):
        """
        Args:
            client: An initialized AsyncAzureOpenAI client.
            model: The deployment name or model identifier.
            temperature: Default temperature.
            top_p: Default top_p.
            supports_reasoning: Explicit override for reasoning capability.
            supports_sampling: Explicit override for sampling parameters support.
        """
        super().__init__(temperature=temperature, top_p=top_p)
        self.client = client
        self.model = model
        self._supports_reasoning_override = supports_reasoning
        self._supports_sampling_override = supports_sampling

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[BackendChunk, None]:
        # Sanitize messages to prevent OpenAI SDK schema validation errors
        clean_messages = []
        for msg in messages:
            clean_msg = {
                "role": msg.get("role"),
                "content": msg.get("content"),
            }
            if "tool_calls" in msg:
                clean_msg["tool_calls"] = msg["tool_calls"]
            if "tool_call_id" in msg:
                clean_msg["tool_call_id"] = msg["tool_call_id"]
            if "name" in msg:
                clean_msg["name"] = msg["name"]
            clean_messages.append(clean_msg)

        kwargs = {}
        if tools:
            kwargs["tools"] = tools

        # Determine sampling parameter capability
        use_sampling = False
        if self._supports_sampling_override is not False:
            if self._supports_sampling_override is True or self.model not in self._unsupported_sampling_models:
                if self.temperature is not None:
                    kwargs["temperature"] = self.temperature
                if self.top_p is not None:
                    kwargs["top_p"] = self.top_p
                use_sampling = True

        # Determine reasoning effort capability
        use_reasoning = False
        thinking_level = "off"
        if options and "thinking_level" in options:
            thinking_level = options["thinking_level"]
            if thinking_level != "off":
                if self._supports_reasoning_override is not False:
                    if self._supports_reasoning_override is True or self.model not in self._unsupported_reasoning_models:
                        if thinking_level in ("low", "medium", "high"):
                            kwargs["reasoning_effort"] = thinking_level
                            use_reasoning = True

        # Retry loop to dynamically fallback when parameters are unsupported by the model
        while True:
            try:
                response_stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=clean_messages,
                    stream=True,
                    **kwargs
                )
                break
            except openai.BadRequestError as e:
                err_msg = str(e)
                if use_reasoning and "reasoning_effort" in err_msg:
                    self._unsupported_reasoning_models.add(self.model)
                    logger.warning(
                        "Thinking level '%s' requested, but model '%s' does not support reasoning_effort. "
                        "Gracefully falling back to execution without reasoning_effort.",
                        thinking_level, self.model
                    )
                    kwargs.pop("reasoning_effort", None)
                    use_reasoning = False
                    continue
                elif use_sampling and ("temperature" in err_msg or "top_p" in err_msg or "sampling" in err_msg):
                    self._unsupported_sampling_models.add(self.model)
                    logger.warning(
                        "Sampling parameters (temperature/top_p) are not supported by model '%s'. "
                        "Gracefully falling back to execution without them.",
                        self.model
                    )
                    kwargs.pop("temperature", None)
                    kwargs.pop("top_p", None)
                    use_sampling = False
                    continue
                else:
                    raise
        
        try:
            async for chunk in response_stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                text_delta = delta.content
                
                tool_calls = None
                if delta.tool_calls:
                    tool_calls = []
                    for tc in delta.tool_calls:
                        tool_calls.append(ToolCallChunk(
                            index=tc.index,
                            id=tc.id,
                            name=tc.function.name if tc.function else None,
                            arguments=tc.function.arguments if (tc.function and tc.function.arguments) else ""
                        ))
                        
                yield BackendChunk(text=text_delta, tool_calls=tool_calls)
        finally:
            # Ensure the connection / stream is closed instantly if execution is aborted
            await response_stream.close()
