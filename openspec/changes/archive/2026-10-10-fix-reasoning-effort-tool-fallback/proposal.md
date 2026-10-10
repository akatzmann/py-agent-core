## Why

Reasoning models (such as `gpt-6.1-sol` and the `o-` series) default reasoning to active on the server side in OpenAI and Azure OpenAI. When invoking `/v1/chat/completions` with function tools, the API forbids active reasoning and returns a 400 error requiring `reasoning_effort` to be set to `'none'`.

Currently, `py_agent_core`'s backend adapters (`AzureOpenAIBackend` and `OpenAIBackend`) fail under this condition in two ways:
1. If `thinking_level` is `"off"` (the default), the error handler is gated behind `if use_reasoning` and never triggers, immediately crashing the agent loop.
2. If `thinking_level` is set, the retry logic simply pops `reasoning_effort`, causing the server default to reactivate and crashing on the second attempt.

This change fixes the fallback logic to set `reasoning_effort="none"`, updates the class-level capability cache, logs an informative warning, and upgrades the `openai` SDK in the local environment.

## What Changes

- **Fix reasoning effort fallback for tools**: Update `AzureOpenAIBackend` and `OpenAIBackend` to catch `BadRequestError` indicating that function tools cannot run with reasoning effort on `/v1/chat/completions`.
- **Set `reasoning_effort="none"` on fallback**: Instead of omitting the parameter (which causes server-side defaults to re-trigger), explicitly set `reasoning_effort="none"` for the retry and cache the model requirement in `_models_requiring_reasoning_none`.
- **Unblock fallback when thinking is off**: Remove the restrictive `if use_reasoning` condition in the exception handler so that server-default reasoning conflicts with tools are caught even when `thinking_level == "off"`.
- **Clear advisory logging**: Emit a structured warning via `logger.warning` explaining that the model does not support combining reasoning tokens with function tools on `/v1/chat/completions`, and that `reasoning_effort` is being forced to `"none"`.
- **Modern Default Model**: Update the default model identifier in `OpenAIBackend` and example CLI scripts from `gpt-4o` to `gpt-6.1-sol`.
- **Upgrade local environment dependency**: Upgrade the `openai` Python SDK in `.venv` to the latest version (`>=3.28.0`) and review/align `pyproject.toml`.
- **Documentation**: Update `README.md` to document compatibility with reasoning models and tool fallback behavior.

## Capabilities

### New Capabilities

<!-- None -->

### Modified Capabilities

- `llm-backends`: Extend the thinking fallback requirement so that when `/v1/chat/completions` rejects function tools due to reasoning effort, `OpenAIBackend` and `AzureOpenAIBackend` gracefully fall back by setting `reasoning_effort="none"`, caching this requirement, and retrying.

## Impact

- **Affected code**: `py_agent_core/backends/azure_openai.py`, `py_agent_core/backends/openai.py`, `tests/test_backend.py`, and `README.md`.
- **APIs**: No breaking API changes. Backend constructors and public interfaces remain backward-compatible.
- **Dependencies**: Upgrades `openai` in the local development environment (`.venv`) and reviews `pyproject.toml`.
