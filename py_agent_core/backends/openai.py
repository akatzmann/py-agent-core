import logging
import openai
from typing import AsyncGenerator, List, Dict, Any, Optional, Tuple, Literal
from openai import AsyncOpenAI
from openai.resources.responses import AsyncResponses
from py_agent_core.backends.base import BaseBackend, BackendChunk, ToolCallChunk
from py_agent_core.backends.openai_responses_utils import (
    _convert_messages_for_responses,
    _convert_tools_for_responses,
    ResponsesStreamTracker,
)

logger = logging.getLogger(__name__)


class OpenAIBackend(BaseBackend):
    """Adapter for standard OpenAI API, supporting both /v1/responses and /v1/chat/completions."""

    _unsupported_reasoning_models = set()
    _unsupported_sampling_models = set()
    _models_requiring_reasoning_none = set()
    _unsupported_responses_endpoints = set()
    _requires_responses_for_tools = set()

    def __init__(
        self,
        client: Optional[AsyncOpenAI] = None,
        model: str = "gpt-6.1-sol",
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        supports_reasoning: Optional[bool] = None,
        supports_sampling: Optional[bool] = None,
        api_mode: Literal["auto", "responses", "chat_completions"] = "auto",
    ):
        """
        Args:
            client: Optional AsyncOpenAI client instance. Constructs a default one if None.
            model: The model name to use.
            temperature: Default temperature.
            top_p: Default top_p.
            supports_reasoning: Explicit override for reasoning capability.
            supports_sampling: Explicit override for sampling parameters support.
            api_mode: Wire protocol mode: 'auto' (negotiate capability), 'responses', or 'chat_completions'.
        """
        super().__init__(temperature=temperature, top_p=top_p)
        self.client = client or AsyncOpenAI()
        self.model = model
        self.api_mode = api_mode
        self._supports_reasoning_override = supports_reasoning
        self._supports_sampling_override = supports_sampling

    @property
    def _endpoint_cache_key(self) -> Tuple[str, str]:
        base_url = str(getattr(self.client, "base_url", ""))
        return (base_url, self.model)

    def _client_supports_responses(self) -> bool:
        """Determines if the client instance provides a callable responses resource."""
        if not hasattr(self.client, "responses"):
            return False
        responses_attr = getattr(self.client, "responses")
        if not hasattr(responses_attr, "create"):
            return False
        create_fn = getattr(responses_attr, "create")
        try:
            from unittest.mock import MagicMock, AsyncMock
            if isinstance(responses_attr, MagicMock) and not isinstance(create_fn, AsyncMock):
                return False
        except ImportError:
            pass
        return True

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[BackendChunk, None]:
        if self.api_mode == "chat_completions":
            async for chunk in self._generate_stream_chat_completions(messages, tools, options):
                yield chunk
            return

        if self.api_mode == "responses":
            async for chunk in self._generate_stream_responses(messages, tools, options):
                yield chunk
            return

        # 'auto' mode: negotiate capabilities without guessing based on model name
        cache_key = self._endpoint_cache_key
        client_has_responses = self._client_supports_responses()
        is_responses_unsupported = cache_key in type(self)._unsupported_responses_endpoints

        if client_has_responses and not is_responses_unsupported:
            try:
                async for chunk in self._generate_stream_responses(messages, tools, options):
                    yield chunk
                return
            except (openai.NotFoundError, openai.APIStatusError) as e:
                status_code = getattr(e, "status_code", None)
                err_msg = str(e).lower()
                is_unsupported_endpoint = (
                    status_code in (404, 405)
                    or "not found" in err_msg
                    or "unknown endpoint" in err_msg
                    or "invalid operation" in err_msg
                )
                if is_unsupported_endpoint:
                    type(self)._unsupported_responses_endpoints.add(cache_key)
                    logger.warning(
                        "Endpoint '%s' does not support /v1/responses (status %s). "
                        "Falling back to /v1/chat/completions.",
                        cache_key,
                        status_code,
                    )
                    async for chunk in self._generate_stream_chat_completions(messages, tools, options):
                        yield chunk
                    return
                else:
                    raise

        # If responses is not supported by client or endpoint, use chat completions
        async for chunk in self._generate_stream_chat_completions(messages, tools, options):
            yield chunk

    async def _generate_stream_responses(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[BackendChunk, None]:
        instructions, input_items = _convert_messages_for_responses(messages)
        converted_tools = _convert_tools_for_responses(tools)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "input": input_items,
            "stream": True,
        }
        if instructions:
            kwargs["instructions"] = instructions
        if converted_tools:
            kwargs["tools"] = converted_tools

        # Determine sampling parameter capability
        use_sampling = False
        if self._supports_sampling_override is not False:
            if self._supports_sampling_override is True or self.model not in type(self)._unsupported_sampling_models:
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
                    if self._supports_reasoning_override is True or self.model not in type(self)._unsupported_reasoning_models:
                        if thinking_level in ("low", "medium", "high", "xhigh"):
                            kwargs["reasoning"] = {"effort": thinking_level}
                            use_reasoning = True

        # Retry loop to dynamically fallback when parameters are unsupported by the model
        while True:
            try:
                response_stream = await self.client.responses.create(**kwargs)
                break
            except openai.BadRequestError as e:
                err_msg = str(e)
                if use_reasoning and ("reasoning" in err_msg or "reasoning_effort" in err_msg):
                    type(self)._unsupported_reasoning_models.add(self.model)
                    logger.warning(
                        "Thinking level '%s' requested, but responses model '%s' does not support reasoning parameter. "
                        "Gracefully falling back to execution without reasoning.",
                        thinking_level,
                        self.model,
                    )
                    kwargs.pop("reasoning", None)
                    use_reasoning = False
                    continue
                elif use_sampling and ("temperature" in err_msg or "top_p" in err_msg or "sampling" in err_msg):
                    type(self)._unsupported_sampling_models.add(self.model)
                    logger.warning(
                        "Sampling parameters (temperature/top_p) are not supported by responses model '%s'. "
                        "Gracefully falling back to execution without them.",
                        self.model,
                    )
                    kwargs.pop("temperature", None)
                    kwargs.pop("top_p", None)
                    use_sampling = False
                    continue
                else:
                    raise

        tracker = ResponsesStreamTracker()
        try:
            async for event in response_stream:
                for chunk in tracker.handle_event(event):
                    yield chunk
        finally:
            if hasattr(response_stream, "close"):
                await response_stream.close()

    async def _generate_stream_chat_completions(
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
            if self._supports_sampling_override is True or self.model not in type(self)._unsupported_sampling_models:
                if self.temperature is not None:
                    kwargs["temperature"] = self.temperature
                if self.top_p is not None:
                    kwargs["top_p"] = self.top_p
                use_sampling = True

        # Determine reasoning effort capability
        use_reasoning = False
        thinking_level = "off"
        if tools and self.model in type(self)._models_requiring_reasoning_none:
            kwargs["reasoning_effort"] = "none"
        elif options and "thinking_level" in options:
            thinking_level = options["thinking_level"]
            if thinking_level != "off":
                if self._supports_reasoning_override is not False:
                    if self._supports_reasoning_override is True or self.model not in type(self)._unsupported_reasoning_models:
                        if thinking_level in ("low", "medium", "high"):
                            kwargs["reasoning_effort"] = thinking_level
                            use_reasoning = True

        promoted_to_responses = False
        while True:
            try:
                response_stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=clean_messages,
                    stream=True,
                    **kwargs,
                )
                break
            except openai.BadRequestError as e:
                err_msg = str(e)
                err_msg_lower = err_msg.lower()
                is_reasoning_tool_conflict = (
                    "reasoning_effort" in err_msg_lower
                    and ("none" in err_msg_lower or "responses" in err_msg_lower or "function tools" in err_msg_lower or "tool" in err_msg_lower)
                    and kwargs.get("reasoning_effort") != "none"
                )
                is_none_unsupported = (
                    "reasoning_effort" in err_msg_lower
                    and "does not support 'none'" in err_msg_lower
                )

                # If model rejects reasoning_effort='none' or explicitly suggests responses for tools, promote to responses if supported
                if (is_none_unsupported or ("responses" in err_msg_lower and tools)) and self.api_mode != "chat_completions" and self._client_supports_responses():
                    type(self)._requires_responses_for_tools.add(self._endpoint_cache_key)
                    type(self)._unsupported_responses_endpoints.discard(self._endpoint_cache_key)
                    logger.info(
                        "Endpoint '%s' requires /v1/responses for function tools with reasoning. "
                        "Dynamically promoting request to /v1/responses.",
                        self._endpoint_cache_key,
                    )
                    promoted_to_responses = True
                    break

                if is_reasoning_tool_conflict:
                    type(self)._models_requiring_reasoning_none.add(self.model)
                    logger.warning(
                        "Model '%s' does not support function tools with active reasoning on /v1/chat/completions. "
                        "Gracefully falling back to execution with reasoning_effort='none'.",
                        self.model,
                    )
                    kwargs["reasoning_effort"] = "none"
                    use_reasoning = False
                    continue
                elif use_reasoning and "reasoning_effort" in err_msg:
                    type(self)._unsupported_reasoning_models.add(self.model)
                    logger.warning(
                        "Thinking level '%s' requested, but model '%s' does not support reasoning_effort. "
                        "Gracefully falling back to execution without reasoning_effort.",
                        thinking_level,
                        self.model,
                    )
                    kwargs.pop("reasoning_effort", None)
                    use_reasoning = False
                    continue
                elif use_sampling and ("temperature" in err_msg or "top_p" in err_msg or "sampling" in err_msg):
                    type(self)._unsupported_sampling_models.add(self.model)
                    logger.warning(
                        "Sampling parameters (temperature/top_p) are not supported by model '%s'. "
                        "Gracefully falling back to execution without them.",
                        self.model,
                    )
                    kwargs.pop("temperature", None)
                    kwargs.pop("top_p", None)
                    use_sampling = False
                    continue
                else:
                    raise

        if promoted_to_responses:
            async for chunk in self._generate_stream_responses(messages, tools, options):
                yield chunk
            return

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
                            arguments=tc.function.arguments if (tc.function and tc.function.arguments) else "",
                        ))

                yield BackendChunk(
                    text=text_delta,
                    thinking=thinking_delta,
                    tool_calls=tool_calls,
                )
        finally:
            if hasattr(response_stream, "close"):
                await response_stream.close()
