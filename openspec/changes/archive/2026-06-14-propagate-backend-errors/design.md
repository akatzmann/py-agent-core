## Context

When the LLM backend client wrapper throws an exception (due to endpoint connection failure, credentials issues, timeout, etc.), the core execution loop in `run_loop` (located in `py_agent_core/agent_loop.py`) catches it, emits an `ErrorEvent`, and returns. Consequently, callers of `Agent.prompt()` or `Agent.prompt_stream()` receive a successful completion without any propagated exceptions.

## Goals / Non-Goals

**Goals:**
- Propagate backend/network exceptions up to the calling application when using modern interfaces (`Agent.prompt`, `Agent.prompt_stream`).
- Ensure the event subscriber system still receives `ErrorEvent`s when an exception is raised.
- Maintain backward compatibility for legacy callers of `PyAgent.run_loop` by catching exceptions and wrapping them in legacy `error` events rather than raising them.

**Non-Goals:**
- Modifying how tool execution errors (exceptions raised by tools themselves) are handled. Tool errors will continue to be caught and returned as tool result messages to the LLM.

## Decisions

### Decision 1: Re-raise exceptions in `run_loop` after emitting `ErrorEvent`
- **What**: In the generation `except Exception as e:` block inside `run_loop` (in `py_agent_core/agent_loop.py`), we will add a `raise` statement after invoking `call_maybe_async(emit, ErrorEvent(str(e)))`.
- **Alternatives Considered**: 
  - *Keep swallowing in `run_loop` but flag the error in AgentState*: This still requires users of `Agent.prompt` to inspect state manually after every invocation, which is unidiomatic.
- **Rationale**: Raising the error ensures that any direct awaiter of `agent_loop` receives the exception, which propagates to `Agent.prompt` and bubbles up to the caller naturally.

### Decision 2: Let `Agent.prompt_stream` propagate background task exceptions
- **What**: `Agent.prompt_stream` runs the agent loop inside a background task `task = asyncio.create_task(run_task())` and pulls events from a queue. We will modify `run_task` to re-raise any exception caught. Then, in the generator loop of `prompt_stream`, after the event queue is drained, we will check if the task has an exception via `task.exception()` and raise it if present.
- **Alternatives Considered**:
  - *Do not run `agent_loop` in a background task*: `prompt_stream` must run the loop concurrently with the client's consumption of the generator, so a separate task is necessary.
- **Rationale**: This guarantees that the stream consumer is interrupted by a real exception on connection/backend failures, while still allowing them to process yielded events leading up to the error.

### Decision 3: Catch exceptions in legacy `PyAgent.run_loop`
- **What**: Wrap the `async for event in self._agent.prompt_stream(user_prompt):` iteration in `PyAgent.run_loop` inside a `try...except Exception as e:` block and yield `LegacyAgentEvent(type="error", content=str(e))`.
- **Rationale**: This keeps the behavior of legacy `PyAgent` completely unchanged for downstream users who expect no thrown exceptions.

## Risks / Trade-offs

- **Risk**: Double error events in legacy interface.
  - *Mitigation*: If `prompt_stream` yields `ErrorEvent` and then raises the exception, `PyAgent.run_loop` could yield a legacy `error` event twice (once when handling the yielded event, and once when catching the raised exception). To prevent this, `PyAgent.run_loop` will only yield a legacy `error` event for the raised exception and ignore the stream's `ErrorEvent`, or we can ensure `prompt_stream` itself does not yield `ErrorEvent` to the queue when it's going to raise the exception, or simply handle the event type check in the legacy wrapper. Let's make `PyAgent.run_loop` filter out stream-yielded `ErrorEvent`s and only yield the legacy `error` event when catching the final exception.
