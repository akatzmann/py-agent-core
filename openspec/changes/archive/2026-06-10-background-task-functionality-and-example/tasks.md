## 1. Core Framework Implementation

- [x] 1.1 Add `_active_agent_ctx` context variable in `py_agent_core/agent.py`
- [x] 1.2 Set and reset the `_active_agent_ctx` in `Agent._run_lifecycle`
- [x] 1.3 Update `tool` decorator and `Tool` class in `py_agent_core/tool.py` to support `execution_mode="background"`
- [x] 1.4 Implement the background interception logic in `Tool.__call__` that schedules execution via `asyncio.create_task` and returns a placeholder status immediately
- [x] 1.5 Implement background completion steering logic that grabs the dynamic `tool_call_id`, interrupts/steers active agents or adds follow-up, and schedules `agent.continue_()`

## 2. Example & Documentation

- [x] 2.1 Create `examples/background_tool.py` demonstrating non-blocking execution with periodic updates
- [x] 2.2 Update `examples/README.md` to document the background tool example and how to run it

## 3. Verification & Testing

- [x] 3.1 Create unit tests verifying the end-to-end background task flow (non-blocking execution, agent steering, context variable lookup) in `tests/test_new_agent.py`
- [x] 3.2 Run pytest to ensure all test cases pass successfully
