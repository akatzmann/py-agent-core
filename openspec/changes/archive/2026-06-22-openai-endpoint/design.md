## Context

Currently, the codebase has concrete backend adapters for `DummyBackend`, `OllamaBackend`, and `AzureOpenAIBackend`. However, a standard `OpenAIBackend` adapter is missing. To support standard OpenAI endpoints, we need a backend that wraps `AsyncOpenAI` from the official `openai` SDK.

## Goals / Non-Goals

**Goals:**
- Implement a new `OpenAIBackend` class in `py_agent_core/backends/openai.py` inheriting from `BaseBackend`.
- Expose the new class in `py_agent_core/backends/__init__.py` and `py_agent_core/__init__.py`.
- Handle message sanitization (filtering extra fields) and mapping of `thinking_level` to the `reasoning_effort` API parameter for models that support it (e.g., `o1`, `o3-mini`).
- Update `examples/utils.py` to allow selecting the standard `openai` backend with CLI arguments.
- Add comprehensive tests in `tests/test_backend.py` to verify streaming, chunk parsing, and option/reasoning effort mapping.

**Non-Goals:**
- Modify or break behavior of existing backends (Ollama, Azure OpenAI, Dummy).

## Decisions

- **Decision 1: Use `AsyncOpenAI` from `openai` SDK**
  - *Alternatives considered:* Direct HTTP requests to `api.openai.com/v1/chat/completions`.
  - *Rationale:* Since `openai` is already a project dependency and used by the Azure OpenAI backend, wrapping the official SDK client is cleaner, less error-prone, and benefits from automatic retry logic and type-safety.
- **Decision 2: Message Sanitization**
  - *Rationale:* Standard OpenAI API rejects custom properties in messages (such as `thinking` traces). We will filter the keys of messages passed to the completion client to only include standard fields: `role`, `content`, `tool_calls`, `tool_call_id`, and `name`.
- **Decision 3: Reasoning Effort Mapping**
  - *Rationale:* For standard OpenAI models like `o1` and `o3-mini`, the `reasoning_effort` parameter is supported. We will map `thinking_level` (`low`, `medium`, `high`) directly to `reasoning_effort`. For other models, we will log a warning.

## Risks / Trade-offs

- [Authentication] → If the API key is not set, client instantiation or completion requests will fail. We will construct the default client in `__init__` via `client = client or AsyncOpenAI()` which automatically reads `OPENAI_API_KEY` from the environment.
