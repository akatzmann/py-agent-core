## 1. Core Implementation in Agent.prompt_stream

- [x] 1.1 Update `event_sink` in `Agent.prompt_stream()` ([py_agent_core/agent.py](file:///notebooks/2026-05-28_PyAgentCore/py_agent_core/agent.py#L295)) to attach an `asyncio.Event` acknowledgment signal to each queued event and await its completion.
- [x] 1.2 Update generator loop in `Agent.prompt_stream()` to unpack event-ack pairs, call `self._process_events(event)`, yield `event`, and trigger `ack.set()` in a `try...finally` block.
- [x] 1.3 Implement cleanup handlers in `prompt_stream()` generator `finally` blocks to release all pending acknowledgments on abort, task cancellation, or generator exit.

## 2. Testing and Verification

- [x] 2.1 Add unit tests verifying that `ToolExecutionStartEvent` is yielded and processed before tool side-effects take place.
- [x] 2.2 Add tests verifying stream abort and cancellation cleanup without hanging background tasks.
