# Tasks — add-minimal-example-and-refine-existing-examples

## Task 1: Create `examples/minimal_coder.py`
- [x] Write the `@tool run_python_code(code)` function with `asyncio.to_thread` user confirmation and subprocess execution.
- [x] Write `async def main()` with suggested-prompt UX, `Agent` setup, and single event loop print.
- [x] Verify the script runs offline (`python -m examples.minimal_coder`) without errors.

## Task 2: Add inline comments to existing examples

- [x] `examples/hello_agent.py` — `reversed(agent.state.messages)` explanation.
- [x] `examples/advanced_agent_features.py` — turn detection, `isatty`, `subscribe`, `follow_up`/`steer`, parallel execution comment.
- [x] `examples/guardrail_streaming.py` — cooperative generator pattern, word-boundary buffer, `agent.abort()`.
- [x] `examples/agent_swarm.py` — `create_task` + `gather` concurrency, reversed messages.
- [x] `examples/self_healing_coder.py` — turn counting, tool result inspection, `sys.executable` rationale.
- [x] `examples/rhetoric_speaker.py` — `run_in_executor` stdin, `agent.abort()` signal, `live_history` threading.
- [x] `examples/structured_streaming.py` — consolidation pattern, JSON safety rationale.

## Task 3: Update `examples/README.md`
- [x] Add `minimal_coder.py` entry to the Examples Index table (section B in Fundamental examples).
- [x] Add the agent-context-prompt block for autonomous agent orientation.
- [x] Add `minimal_coder` to the offline run command list.
