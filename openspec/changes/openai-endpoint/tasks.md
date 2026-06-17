## 1. Backend Adapter Implementation

- [x] 1.1 Create `py_agent_core/backends/openai.py` implementing `OpenAIBackend`
- [x] 1.2 Export `OpenAIBackend` in `py_agent_core/backends/__init__.py`
- [x] 1.3 Export `OpenAIBackend` in `py_agent_core/__init__.py`

## 2. Examples and Utilities Integration

- [x] 2.1 Update `examples/utils.py` to support `openai` as a choice for `--backend` and map it appropriately

## 3. Testing and Verification

- [x] 3.1 Write unit tests in `tests/test_backend.py` to cover `OpenAIBackend` streaming, tool calls, and `reasoning_effort` mapping
- [x] 3.2 Run the test suite using pytest to verify implementation correctness
