## 1. Implement Coercion in OllamaBackend

- [x] 1.1 Update `py_agent_core/backends/ollama.py` to parse `arguments` string and ensure it is always mapped to a dictionary (using a fallback dictionary wrapper if parsing fails or yields a non-dict type).

## 2. Testing and Verification

- [x] 2.1 Add unit tests in `tests/test_backend.py` to verify that `OllamaBackend.generate_stream` successfully handles messages with string and list tool call arguments without raising a Pydantic `ValidationError`.
- [x] 2.2 Verify that the fallback dictionary wrapper propagates as expected and causes the expected `TypeError` when calling the tool function in `tests/test_agent.py`.
- [x] 2.3 Run the entire test suite using `PYTHONPATH=. .venv/bin/pytest` and verify all tests pass.
