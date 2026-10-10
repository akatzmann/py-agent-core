## 1. Environment & Dependencies

- [x] 1.1 Upgrade `openai` to `>=3.28.0` in the local `.venv` and review/update dependency specifications in `pyproject.toml`
- [x] 1.2 Verify that all existing unit tests continue to pass with the upgraded `openai` package

## 2. Backend Fallback Implementation

- [x] 2.1 Add `_models_requiring_reasoning_none` class cache and upfront tool parameter check in `AzureOpenAIBackend` (`py_agent_core/backends/azure_openai.py`)
- [x] 2.2 Update `BadRequestError` exception handling in `AzureOpenAIBackend` to set `reasoning_effort="none"` and emit a warning when tools conflict with reasoning
- [x] 2.3 Add `_models_requiring_reasoning_none` class cache and upfront tool parameter check in `OpenAIBackend` (`py_agent_core/backends/openai.py`)
- [x] 2.4 Update `BadRequestError` exception handling in `OpenAIBackend` to set `reasoning_effort="none"` and emit a warning when tools conflict with reasoning
- [x] 2.5 Update default model in `OpenAIBackend` and example CLI utils to `gpt-6.1-sol` (replacing deprecated `gpt-4o`)

## 3. Unit Tests & Verification

- [x] 3.1 Add unit test in `tests/test_backend.py` for fallback to `reasoning_effort="none"` when `thinking_level` is explicitly set
- [x] 3.2 Add unit test in `tests/test_backend.py` for fallback to `reasoning_effort="none"` when `thinking_level` is `"off"` (server-default reasoning)
- [x] 3.3 Add unit test in `tests/test_backend.py` verifying proactive setting of `reasoning_effort="none"` on subsequent calls for cached models
- [x] 3.4 Run the complete test suite to ensure all unit tests pass without regressions

## 4. Documentation

- [x] 4.1 Update `README.md` to document reasoning model compatibility and tool fallback behavior on `/v1/chat/completions`
