## 1. Core Loop Error Handling

- [x] 1.1 Raise backend exceptions in `run_loop` inside `py_agent_core/agent_loop.py` after emitting `ErrorEvent` in generator loop

## 2. Modern Agent Class Exception Propagation

- [x] 2.1 Update `prompt_stream` inside `py_agent_core/agent.py` to check `task.exception()` and raise it to propagate backend errors to stream consumers

## 3. Legacy Wrapper Compatibility

- [x] 3.1 Wrap stream consumption in `PyAgent.run_loop` inside `py_agent_core/agent.py` to catch raised exceptions and yield a legacy error event, avoiding duplicate events

## 4. Verification

- [x] 4.1 Write unit tests in `tests/test_new_agent.py` verifying that modern `prompt()` and `prompt_stream()` raise backend exceptions, and legacy `PyAgent` yields them as compatibility events
- [x] 4.2 Run unit tests and verify they pass
