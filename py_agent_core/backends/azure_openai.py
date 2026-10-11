import logging
from typing import Optional, Literal
from openai import AsyncAzureOpenAI
from py_agent_core.backends.openai import OpenAIBackend

logger = logging.getLogger(__name__)


class AzureOpenAIBackend(OpenAIBackend):
    """Adapter for Microsoft Azure OpenAI Service, supporting both /v1/responses and /v1/chat/completions."""

    _unsupported_reasoning_models = set()
    _unsupported_sampling_models = set()
    _models_requiring_reasoning_none = set()
    _unsupported_responses_endpoints = set()
    _requires_responses_for_tools = set()

    def __init__(
        self,
        client: AsyncAzureOpenAI,
        model: str,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        supports_reasoning: Optional[bool] = None,
        supports_sampling: Optional[bool] = None,
        api_mode: Literal["auto", "responses", "chat_completions"] = "auto",
    ):
        """
        Args:
            client: An initialized AsyncAzureOpenAI client.
            model: The deployment name or model identifier.
            temperature: Default temperature.
            top_p: Default top_p.
            supports_reasoning: Explicit override for reasoning capability.
            supports_sampling: Explicit override for sampling parameters support.
            api_mode: Wire protocol mode: 'auto' (negotiate capability), 'responses', or 'chat_completions'.
        """
        super().__init__(
            client=client,
            model=model,
            temperature=temperature,
            top_p=top_p,
            supports_reasoning=supports_reasoning,
            supports_sampling=supports_sampling,
            api_mode=api_mode,
        )
