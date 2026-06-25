## 1. Core Implementation

- [x] 1.1 Add stream-local list `known_tool_calls = []` inside `OllamaBackend.generate_stream` in `py_agent_core/backends/ollama.py`.
- [x] 1.2 Implement sequential tool call matching using name and argument prefix check to assign unique stable indices (`fallback_{idx}_{name}`).
- [x] 1.3 Calculate the arguments delta against the correct matched tool call's accumulated arguments.


## 2. Testing and Verification

- [x] 2.1 Add a unit test in `tests/test_backend.py` simulating sequential non-cumulative tool call streams where every chunk contains a single tool call with different arguments.
- [x] 2.2 Run pytest to ensure all test cases pass successfully.
