## ADDED Requirements

### Requirement: Advanced Orchestrator Features Example
The system SHALL provide an advanced orchestration example script demonstrating decoupled telemetry subscription, interactive before-tool execution gates, after-tool outcome auditing, parallel tool execution, custom translation pipelines, active steering queues, and follow-up queues.

#### Scenario: Event subscription and console logging
- **WHEN** the agent streams events during a run and a telemetry subscriber callback is registered
- **THEN** the system SHALL invoke the subscriber callback for each lifecycle event (such as turn start, message update, and tool execution) without blocking or mutating the core response generation.

#### Scenario: Intercepting tool execution via before-tool hook
- **WHEN** a tool call is scheduled for execution and a `before_tool_call` interceptor hook is registered
- **THEN** the system SHALL execute the hook to inspect the tool call and allow it to run, block it, or abort the agent run based on user confirmation.

#### Scenario: Auditing and modifying tool output via after-tool hook
- **WHEN** a tool execution completes and an `after_tool_call` hook is registered
- **THEN** the system SHALL execute the hook to inspect the tool result, potentially rewriting the output or setting a termination flag before feeding it back to the LLM.

#### Scenario: Parallel tool execution
- **WHEN** the agent loop receives multiple independent tool calls in a single turn and parallel tool execution is enabled
- **THEN** the system SHALL execute the tools concurrently and yield tool start and end events for all active calls.

#### Scenario: Translation and context pruning pipelines
- **WHEN** the conversation contains custom message types or exceeds history thresholds, and translation hooks are registered
- **THEN** the system SHALL invoke `convert_to_llm` to map custom message objects to LLM messages, and `transform_context` to prune or summarize the history prior to translation.

#### Scenario: Mid-turn steering and follow-up queuing
- **WHEN** steering messages are injected via `steer()` or follow-up prompts are queued via `follow_up()`
- **THEN** the system SHALL process these queued messages sequentially at the respective turn boundaries and continue executing the agent loop.
