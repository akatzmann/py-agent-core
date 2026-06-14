# Delta Spec — add-minimal-example-and-refine-existing-examples

## New File: `examples/minimal_coder.py`

A minimal, single-screen example showing the full `@tool` → user confirmation → `Agent.prompt_stream()` loop.

### Requirements

1. **Length**: ≤ 35 meaningful lines (excluding blank lines and the standard `if __name__ == "__main__"` block).
2. **Imports**: Only `asyncio`, `py_agent_core` (`Agent`, `tool`), and `examples.utils` (`get_backend_from_args`).
3. **Tool**: One `@tool` decorated async function `run_python_code(code: str) -> str` that:
   - Uses `asyncio.to_thread(input, ...)` to ask for user confirmation **without blocking the event loop**.
   - On rejection, returns a descriptive string instead of aborting (keeps the agent loop running for a graceful denial message).
   - Executes the code via `asyncio.create_subprocess_exec(sys.executable, "-c", code, ...)` on approval.
4. **UX**: Print a suggested task prompt (`"What is the factorial of 12?"`), then `input()` for the actual task, defaulting to the suggestion on empty input.
5. **Agent setup**: One `Agent(backend, initial_state={...tools..., systemPrompt...})`.
6. **Main loop**: Single `async for event in agent.prompt_stream(task):` that prints `text_delta` events and a completion message.
7. **No custom DummyBackend subclass** — keep it truly minimal.

### Non-Functional Requirements

- Must run offline with `DummyBackend` (no live API needed).
- Must be runnable as: `python -m examples.minimal_coder`.

---

## Modified File: `examples/hello_agent.py`

No logic changes. Add/improve inline comments only:
- Explain why `reversed(agent.state.messages)` is used (most recent last).

---

## Modified File: `examples/advanced_agent_features.py`

No logic changes. Add/improve inline comments only:
- `generate_stream()` override: explain how turn number is detected via `len(user_msgs)` / `len(tool_msgs)`.
- `human_approval_gate`: explain why `sys.stdin.isatty()` is checked (CI/CD safety).
- `agent.subscribe()`: explain that callbacks fire for **every** event, not just lifecycle transitions.
- `agent.follow_up()` vs `agent.steer()`: explain the semantic difference.
- `tool_execution="parallel"`: explain that tool calls within a single turn run concurrently.

---

## Modified File: `examples/guardrail_streaming.py`

No logic changes. Add/improve inline comments only:
- Generator wrapper pattern (`async def guardrail_filter(agent_loop, agent)`): explain that this is a **cooperative async generator** that intercepts events by re-yielding them.
- Word-boundary flush logic: explain the split/rejoin buffer strategy for streaming regex safety.
- `agent.abort()`: explain that this signals the agent loop to stop generating.

---

## Modified File: `examples/agent_swarm.py`

No logic changes. Add/improve inline comments only:
- `asyncio.create_task()` + `asyncio.gather()`: explain why tasks are created first (to allow true concurrency) and then gathered.
- `reversed(event.messages)`: explain the linear message stack convention.

---

## Modified File: `examples/self_healing_coder.py`

No logic changes. Add/improve inline comments only:
- `CoderDummyBackend.generate_stream()`: explain the turn-counting mechanism via `len(tool_msgs)`.
- Tool result inspection: explain how the loop reads `tool_msgs[-1]["content"]` to decide next action.
- `asyncio.create_subprocess_exec()`: clarify why `sys.executable` is used instead of `"python"` (virtualenv safety).

---

## Modified File: `examples/rhetoric_speaker.py`

No logic changes. Add/improve inline comments only:
- `input_listener`: explain why `loop.run_in_executor(None, sys.stdin.readline)` is used (non-blocking stdin in async context).
- `agent.abort()`: explain that abort sets a signal checked on the next event yield.
- `live_history` management: explain why history is threaded manually across agent instances.

---

## Modified File: `examples/structured_streaming.py`

No logic changes. Add/improve inline comments only:
- `reversed(agent.state.messages)` for final consolidation: explain pattern.
- `json.loads(assistant_content)`: explain why we consolidate from history rather than building a string from deltas (avoids partial-token JSON).

---

## Modified File: `examples/README.md`

- Update "Examples Index & Demos" table to include the new `minimal_coder.py` entry.
- Add the new agent-context-prompt block under the Examples section (mirroring the root README's "Context Delegation" block).
