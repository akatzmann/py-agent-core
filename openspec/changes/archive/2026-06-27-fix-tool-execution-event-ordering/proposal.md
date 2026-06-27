## Why

When consuming event streams from `Agent.prompt_stream()`, events emitted by the internal background task (`agent_loop`) are currently pushed to an unbuffered `asyncio.Queue` without awaiting consumer processing. As a result, when tools execute synchronous side-effects (such as terminal PTY streaming to stdout or interactive user prompts), the side-effects execute in the OS process before the downstream consumer task receives and yields `ToolExecutionStartEvent`.

This causes event out-of-order execution in downstream UI applications (like `slash-agent`), rendering tool output on screen before the UI can render execution start headers/badges.

## What Changes

- Implement a **Full Rendezvous Event Synchronization** mechanism within `Agent.prompt_stream()` in `py_agent_core/agent.py`.
- Ensure every event pushed to the streaming queue blocks `agent_loop` until the consumer generator yields the event to the downstream caller.
- Ensure pending event acknowledgments are cleanly released upon abort, task cancellation, or generator termination to prevent background task hangs.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `core-runner`: Update event streaming requirements to specify deterministic rendezvous event delivery during `Agent.prompt_stream()`.

## Impact

- `py_agent_core/agent.py`: Modification of `prompt_stream()` event sink and generator yield loop.
- Downstream CLI applications (e.g., `slash-agent`): Guarantees strictly deterministic event ordering where execution headers render prior to tool execution stdout output.
