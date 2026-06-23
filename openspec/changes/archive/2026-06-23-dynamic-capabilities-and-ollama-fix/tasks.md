## 1. Ollama Tool Streaming Fix

- [x] 1.1 Update `OllamaBackend.generate_stream` to initialize stable indices mapping and yielded arguments tracking.
- [x] 1.2 Update the `raw_tool_calls` loop in `OllamaBackend.generate_stream` to compute argument deltas and yield them with stable, chunk-independent indexes.
- [x] 1.3 Add code comments in `OllamaBackend.generate_stream` explaining the stable indexing and delta calculation logic.

## 2. OpenAI and Azure OpenAI Capability Probing & Fallback

- [x] 2.1 Update `OpenAIBackend` and `AzureOpenAIBackend` constructors to accept `supports_reasoning` and `supports_sampling`.
- [x] 2.2 Define class-level caches `_unsupported_reasoning_models` and `_unsupported_sampling_models` on `OpenAIBackend` and `AzureOpenAIBackend`.
- [x] 2.3 Update `generate_stream` in `openai.py` and `azure_openai.py` to wrap the chat completions request in a try-except block catching `openai.BadRequestError`, log a warning once, update cache, and retry without the unsupported parameter.
- [x] 2.4 Document `supports_reasoning` and `supports_sampling` parameters in the docstrings of `OpenAIBackend` and `AzureOpenAIBackend`.

## 3. Ollama Backend Capability Probing & Fallback

- [x] 3.1 Update `OllamaBackend` constructor to accept `supports_reasoning`.
- [x] 3.2 Define class-level cache `_unsupported_reasoning_models` on `OllamaBackend`.
- [x] 3.3 Update `generate_stream` in `ollama.py` to wrap `client.chat` call in a try-except block catching `ollama.ResponseError`, log a warning once, update cache, and retry without the thinking parameter.
- [x] 3.4 Document `supports_reasoning` parameter in the docstring of `OllamaBackend`.

## 4. Documentation and README Updates

- [x] 4.1 Add a high-level `[!TIP]` note in `README.md` under the "Swapping Backends" section mentioning the automatic fallback and constructor override capabilities, keeping detailed API documentation in the constructor docstrings.

## 5. Tests and Verification

- [x] 5.1 Update `test_openai_backend_non_reasoning_model` in `tests/test_backend.py` to raise `BadRequestError` for `reasoning_effort` and verify it falls back correctly.
- [x] 5.2 Add new test case `test_ollama_backend_tool_streaming_index_and_delta` to verify stable indices and argument slicing.
- [x] 5.3 Add new test case `test_openai_backend_sampling_unsupported_fallback` to verify sampling fallback and single-time warning logging.
- [x] 5.4 Run all tests using `PYTHONPATH=. .venv/bin/pytest` and verify success.
