## Context

`Agent.prompt_stream()` launches `agent_loop` in a background asyncio task (`run_task`) and passes an `event_sink` callback as `loop_config.emit`. `event_sink` places events onto an `asyncio.Queue`, and `prompt_stream()` iterates through the queue yielding events to downstream callers.

Currently, `event_sink` performs non-blocking `await queue.put(event)`. On an unbounded queue, this returns synchronously without suspending `run_task`. As a result, `agent_loop` immediately proceeds into tool execution callbacks before the `prompt_stream` task is scheduled to yield `ToolExecutionStartEvent`.

## Goals / Non-Goals

**Goals:**
- Guarantee 100% deterministic event delivery ordering in `prompt_stream()`.
- Ensure `ToolExecutionStartEvent` is yielded and processed downstream before tool execution side-effects begin.
- Maintain single-responsibility clean code without modifying `agent_loop.py`.
- Handle abort signals and generator cleanup safely without hanging tasks.

**Non-Goals:**
- Modifying the low-level `agent_loop()` core loop function.
- Changing event delivery mechanics for non-streaming `prompt()` or `continue_()` invocations.

## Decisions

### Decision 1: Full Rendezvous Acknowledged Delivery via `asyncio.Event`
**Choice**: In `prompt_stream()`, `event_sink` will create an `asyncio.Event()` ack signal for each emitted event, pair it with the event in the queue, and `await ack.wait()` before returning to `agent_loop`. `prompt_stream()` will call `ack.set()` in a `finally` block after `yield event` completes.

**Rationale**:
- Eliminates all race conditions across task scheduling ticks.
- Guarantees universal state synchronization between agent loop state and downstream UI state.
- Completely isolated to `prompt_stream()` in `py_agent_core/agent.py`.

**Alternatives Considered**:
- *Selective Boundary Acknowledgment*: Only acknowledge tool start/end events. Rejected to maintain architectural purity, avoid hardcoded event type checks in queue transport, and preserve uniform system invariants.
- *Cooperative Yielding (`asyncio.sleep(0)`)*: Relinquishing execution tick without explicit acknowledgment. Rejected because task scheduling under load is non-deterministic.

### Decision 2: Abort and Cleanup Synchronization
**Choice**: Store active pending `ack` events or track them in the generator context. When `abort()` is called or the generator exits/closes (in `finally`), set all pending `ack` events so `run_task` is unblocked immediately to process cancellation/abort.

**Rationale**: Prevents deadlocks or hung background tasks when streaming is cancelled mid-turn.

## Risks / Trade-offs

- **[Risk]** Potential deadlock if `prompt_stream` exits prematurely while `run_task` awaits an `ack`.
  - *Mitigation*: Comprehensive cleanup in `finally` blocks in `prompt_stream()` ensuring all pending ack signals are set upon generator exit.
