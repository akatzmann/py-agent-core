## Why

Currently, all tool executions in `py-agent-core` (both `parallel` and `sequential`) are synchronous from the perspective of the agent loop. The runner blocks and waits for all tool calls in a turn to complete before the agent can generate its next response or accept new messages. There is no native support for long-running tools that can execute in the background without blocking the agent's turn flow.

## What Changes

- Introduce a new tool execution mode `"background"`.
- Add context-tracking mechanism (`_active_agent_ctx`) to track the currently running agent loop, allowing background tools to retrieve the active agent instance dynamically without adding boilerplate parameters to the tool function signature.
- Implement a background task wrapper/orchestration flow: when a tool is executed in background mode, it immediately returns a status message, starts execution of the actual tool in a background asyncio task, and later interrupts/steers the agent with the tool result once the execution finishes.
- Add an example demonstrating background tool execution.
- Add comprehensive test cases to verify execution flow, agent interruption, steering, and context variable safety.

## Capabilities

### New Capabilities
*(None)*

### Modified Capabilities
- `tool-execution-control`: Introduce background non-blocking tool execution mode that executes tools in the background, returns status immediately, interrupts/steers the agent once finished, and resumes agent loop processing.

## Impact

- `py_agent_core/tool.py`: Add support for `execution_mode="background"`.
- `py_agent_core/agent.py` and `py_agent_core/agent_loop.py`: Implement agent active-context tracking using `ContextVar`, handle background execution routing, status reporting, and safe agent interruption/steering/resumption.
- Tests and examples directories.
