## 1. Core Interfaces and Types

- [x] 1.1 Update `BackendChunk` in `py_agent_core/backends/base.py` to include `thinking: Optional[str] = None`
- [x] 1.2 Update `BaseBackend.generate_stream` signature in `py_agent_core/backends/base.py` to accept `options: Optional[Dict[str, Any]] = None`

## 2. Model Adapters Implementation

- [x] 2.1 Update `OllamaBackend` in `py_agent_core/backends/ollama.py` to support `options` (translate `thinking_level` to `think`) and sanitize message history of previous thinking traces before requesting completion
- [x] 2.2 Update `OllamaBackend` streaming loop to read the `thinking` field from response chunks and yield it via `BackendChunk`
- [x] 2.3 Update `AzureOpenAIBackend` in `py_agent_core/backends/azure_openai.py` to support `options` (translate `thinking_level` to `reasoning_effort`)
- [x] 2.4 Update `DummyBackend` in `py_agent_core/backends/dummy.py` to support `options` parameter in `generate_stream`

## 3. Agent Loop and Orchestrator Integration

- [x] 3.1 Update `AgentLoopTurnUpdate` and functional runner in `py_agent_core/agent_loop.py` to propagate the active `thinking_level` config as part of options to `generate_stream`
- [x] 3.2 Update `run_loop` streaming loop in `py_agent_core/agent_loop.py` to handle `chunk.thinking`, accumulating it in the assistant message, and emitting `MessageUpdateEvent` with `thinking_delta` type updates

## 4. Verification and Testing

- [x] 4.1 Write unit tests in `tests/test_backend.py` to verify `OllamaBackend` parses the stream `thinking` field and maps options correctly
- [x] 4.2 Write unit tests in `tests/test_agent.py` to verify the agent loop successfully propagates `thinking_level`, accumulates reasoning traces, and emits `thinking_delta` events
