## Context

The current `py-agent-core` codebase implements a basic, monolithic agent loop that lacks parallel execution, lifecycle hooks, and context translation pipelines. This design aligns the library with the reference `@earendil-works/pi-agent-core` architecture while preserving simple Pythonic patterns.

## Goals / Non-Goals

**Goals:**
- **Layered Design**: Separate the stateless async execution generator `agent_loop` / `agent_loop_continue` from the stateful `Agent` orchestrator class.
- **Unified Event Pipeline**: Emit high-fidelity event classes covering the entire turn lifecycle.
- **Concurrent Execution**: Run tool calls concurrently using `asyncio.gather` when configured for parallel execution.
- **Interceptor Hooks**: Provide hook hooks (`before_tool_call`, `after_tool_call`) for auditing and control.
- **Context Pipelines**: Introduce `convert_to_llm` and `transform_context` for custom message architectures.
- **Steering / Queue API**: Support `steer()` and `follow_up()` reactive message queues.

**Non-Goals:**
- Implementing TypeScript-specific features like declaration merging (which isn't native to Python; Python will use standard dicts/objects or generic types instead).
- Rewriting the underlying model adapters/backends (we keep the current `BaseBackend`, `AzureOpenAIBackend`, and `OllamaBackend` interfaces, simply adapting them to output the new granular chunk formats).

## Decisions

### 1. Dual-Purpose Invocation Model
- **Choice**: The `Agent.prompt()` method will perform state updates, notify registered subscription callbacks, and *also* return an async generator yielding the events.
- **Rationale**: This preserves the simple `async for event in agent.prompt(...)` pythonic pattern while supporting the subscription-based decoupled architecture of the reference package.

### 2. Async Concurrency for Parallel Tools
- **Choice**: Use `asyncio.gather` with optional exception handling to run tool executions concurrently in `parallel` mode.
- **Rationale**: Leverages Python's native async task management without requiring external process/thread pools, keeping dependencies light.

### 3. Hook & Callback signatures
- **Choice**: Define callbacks using Python's `Callable` type hints and support both synchronous and asynchronous functions for hooks like `before_tool_call`, `after_tool_call`, `convert_to_llm`, `transform_context`, `prepare_next_turn`, and `should_stop_after_turn`.
- **Rationale**: Provides maximum developer convenience since user hooks might require network/DB calls (async) or simple string filtering (sync).

## Risks / Trade-offs

- **[Risk] Parallel tool run exceptions** → *Mitigation*: If a tool raises an exception, catch it, log it, yield `tool_execution_end` with `is_error=True`, and pass the error message back to the LLM instead of crashing the entire batch of concurrent tools.
- **[Risk] Event backward-compatibility** → *Mitigation*: The change will be a major version bump. Legacy events (`text_delta`, `tool_start`, `tool_end`, etc.) will be deprecated in favor of the new event vocabulary, but we will print clear deprecation warnings if legacy methods are called.
