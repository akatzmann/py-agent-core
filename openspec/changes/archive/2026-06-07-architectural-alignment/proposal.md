## Why

The current `py-agent-core` library lacks high-level production features present in the reference `pi-agent-core` implementation (parallel tool execution, interceptor hooks, customizable message/context mapping, and queue-based steering). Aligning the architectures ensures the Python library provides feature parity and the same premium agent workflows, while keeping simple console-based usage as straightforward as it is today.

## What Changes

- **Rich Event Schema**: Expand the event vocabulary from basic execution outputs to a full turn lifecycle (`agent_start`, `turn_start`, `message_start/update/end`, `tool_execution_start/update/end`, `turn_end`, `agent_end`).
- **Context Pipelines**: Introduce customizable message parsing and context transformation hooks (`convert_to_llm` and `transform_context`) to support non-LLM UI messages in session history.
- **Enhanced Tool Runtime**: Add support for concurrent/parallel tool execution, tool interception middleware (`before_tool_call` and `after_tool_call`), and early loop termination signals (`terminate`).
- **Steering and Follow-up Queues**: Decouple interactive preemptive overrides and turn chaining from the synchronous execution loop using dedicated steering and follow-up message queues.

## Capabilities

### New Capabilities
- `tool-execution-control`: Concurrent tool calling support and hook systems (`before_tool_call`, `after_tool_call`) for auditing, authorization, and early loop termination.
- `context-pipelines`: Context transformations and translation between custom rich messages (`AgentMessage` objects) and standard LLM payloads.
- `control-queues`: Message-driven queue mechanisms (`steer()`, `follow_up()`) for non-blocking mid-execution steering and turn chaining.

### Modified Capabilities
- `core-runner`: Redesign the `PyAgent` loop to yield granular lifecycle events, support reactive subscriptions, and manage separate low-level (`agent_loop`) and high-level (`Agent`) interfaces.

## Impact

- **Affected Code**: `py_agent_core/agent.py`, `py_agent_core/tool.py`, `py_agent_core/__init__.py`.
- **API Impact**: **BREAKING** changes to `PyAgent` initialization arguments and `run_loop` yield signatures to align with the state-subscription model.
- **Dependencies**: No new external runtime dependencies; standard library (`asyncio`) will be leveraged for concurrency.
