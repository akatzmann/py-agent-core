## Context

Currently, `py-agent-core` tool calls are awaited synchronously within the agent turn loop. To allow tools to run asynchronously in the background while the agent continues to converse or remain idle, we need a mechanism to launch background tasks, associate them with the active agent, and inject the results when they finish.

To keep developer APIs clean, this functionality should be annotated as `@tool(execution_mode="background")` without requiring the tool function signature to accept the `agent` instance.

## Goals / Non-Goals

**Goals:**
- Implement `@tool(execution_mode="background")` decorator option.
- Use `contextvars.ContextVar` to track the active `Agent` instance executing a tool call so it can be retrieved by the decorator without adding boilerplates to the function signature.
- Intercept the tool call inside the `Tool` class execution phase if the mode is `"background"`:
  - Immediately return a message indicating the task started.
  - Schedule the actual tool execution to run in the background via `asyncio.create_task`.
  - When the background execution finishes, check if the agent is busy. If it is, abort the active run, steer it with the `toolResult`, and continue the loop. If the agent is idle, register the `toolResult` as a follow-up and trigger `continue_()`.
- Add a clear example demonstrating background tools in the repository.
- Write robust unit tests verifying the end-to-end background task flow.

**Non-Goals:**
- Implementing multi-process or distributed task queues (e.g., Celery, Redis). All execution remains in-process using `asyncio` task scheduling.

## Decisions

### Decision 1: Use `contextvars.ContextVar` to store and access the active Agent instance
- **Rationale**: Keeps tool definitions decoupled. Tool functions do not need to accept an `agent` parameter or be bound to a specific agent instance at definition/import time.
- **Alternatives Considered**: 
  - *Dependency Injection*: Passing `agent` to the tool call parameters. This pollutes the tool function signature and exposes internal orchestrator detail to the tool logic.
  - *Stateful Tool Binding*: Binding the agent to the `Tool` instance during `Agent` construction. This is less elegant and can make sharing the same tool instance across multiple agents difficult or error-prone.

### Decision 2: Implement background logic in the `Tool.__call__` wrapper rather than the core loop
- **Rationale**: Keeps the core engine runner (`agent_loop.py`) simple and unaware of background execution mechanics. The core runner calls the tool (which is the wrapped function). The wrapper returns a status string immediately (like `"Task started..."`) and schedules the background task.
- **Alternatives Considered**: 
  - *Core runner interception*: Intercepting the call in `execute_tool_calls_parallel` and `execute_tool_calls_sequential`. This pollutes the core loop with background-specific task-scheduling and steering logic.

### Decision 3: Retrieve `tool_call_id` dynamically from agent history
- **Rationale**: Since the wrapper runs during the tool execution phase, the assistant message has already been appended to the agent's history. The wrapper can find its corresponding `tool_call_id` by matching the tool name in `agent.state.messages[-1]`.

## Risks / Trade-offs

- **Risk**: A background task finishes while the agent is actively generating a response.
  - *Mitigation*: The background completion handler aborts the current run, waits for the agent to settle to an idle state (`wait_for_idle`), and then steers the agent using `agent.steer` and starts `agent.continue_()`.
- **Risk**: Context leak across agents.
  - *Mitigation*: Use standard ContextVar set/reset tokens in `_run_lifecycle` to clean up the context after every run loop execution.
