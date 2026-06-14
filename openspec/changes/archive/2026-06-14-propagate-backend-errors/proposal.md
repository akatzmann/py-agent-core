## Why

Currently, when the LLM backend generation stream encounters an exception (e.g., network unreachability, invalid API keys, or an incorrect model name), the execution loop catches the exception, emits an `ErrorEvent`, and silently returns. Downstream callers awaiting `Agent.prompt()` or iterating over `Agent.prompt_stream()` receive no exception, making it impossible to implement standard error handling, retry policies, or fallback strategies.

## What Changes

- **Propagate Backend Errors**: Modify `run_loop` in the asynchronous execution loop to propagate backend exceptions rather than swallowing them.
- **Maintain Event Emission**: Ensure `ErrorEvent` is still emitted before propagating the exception so that active subscribers are notified of the error.
- **Legacy Compatibility**: Ensure that the legacy `PyAgent.run_loop` compatibility layer handles exceptions internally and yields `LegacyAgentEvent(type="error", ...)` instead of raising the error, preserving historical behavior for legacy downstream users.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `core-runner`: Update the execution loop behavior to propagate infrastructure/backend errors to modern calling interfaces while preserving event emission and legacy compatibility.

## Impact

- **Affected Code**: `py_agent_core/agent_loop.py` (specifically `run_loop`), `py_agent_core/agent.py` (specifically `Agent.prompt_stream` and `PyAgent.run_loop`).
- **APIs**: Modern `Agent.prompt()` and `Agent.prompt_stream()` will now raise errors when backend generation fails. Legacy `PyAgent.run_loop()` will continue to yield `error` events without raising exceptions.
