import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
from openai import AsyncOpenAI
from py_agent_core.backends.base import BaseBackend, BackendChunk, ToolCallChunk

logger = logging.getLogger(__name__)

class OpenAIBackend(BaseBackend):
    """Adapter for standard OpenAI API."""
    
    def __init__(
        self,
        client: Optional[AsyncOpenAI] = None,
        model: str = "gpt-4o",
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ):
        """
        Args:
            client: Optional AsyncOpenAI client instance. Constructs a default one if None.
            model: The model name to use.
        """
        super().__init__(temperature=temperature, top_p=top_p)
        self.client = client or AsyncOpenAI()
        self.model = model

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

        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if self.top_p is not None:
            kwargs["top_p"] = self.top_p

        if options and "thinking_level" in options:
            thinking_level = options["thinking_level"]
            if thinking_level != "off":
                model_lower = self.model.lower()
                if "o1" in model_lower or "o3" in model_lower:
                    if thinking_level in ("low", "medium", "high"):
                        kwargs["reasoning_effort"] = thinking_level
                else:
                    logger.warning(
                        "Thinking level '%s' requested, but model '%s' may not support reasoning_effort. "
                        "Only OpenAI o1/o3-mini models support reasoning_effort.",
                        thinking_level, self.model
                    )

        response_stream = await self.client.chat.completions.create(
            model=self.model,
            messages=clean_messages,
            stream=True,
            **kwargs
        )
        
        try:
            async for chunk in response_stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                text_delta = delta.content
                thinking_delta = getattr(delta, "reasoning_content", None)
                
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
                        
                yield BackendChunk(
                    text=text_delta,
                    thinking=thinking_delta,
                    tool_calls=tool_calls
                )
        finally:
            await response_stream.close()
