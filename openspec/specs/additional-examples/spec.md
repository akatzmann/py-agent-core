# additional-examples Specification

## Purpose
TBD - created by archiving change additional-examples. Update Purpose after archive.
## Requirements
### Requirement: Interactive Chat TUI Example
The system SHALL provide an interactive command-line/TUI chat example script that decouples user typing input from the asynchronous streaming of agent tokens and handles real-time preemption upon user input.

#### Scenario: TUI streams tokens and accepts typing
- **WHEN** the agent is actively streaming response tokens and the user typing prompt is displayed at the bottom
- **THEN** the system SHALL render the streaming text tokens in the scrollable log area without displacing the user's active cursor or input line.

#### Scenario: TUI interrupt triggers preemption
- **WHEN** the user types characters while the agent is streaming tokens
- **THEN** the system SHALL immediately call the agent's interrupt method to halt streaming.

### Requirement: Guardrail Interception Example
The system SHALL provide a stream filtering/guardrail example script that intercepts token events, redacts sensitive pattern matching, and interrupts execution if blocked keywords are detected.

#### Scenario: Guardrail redacts sensitive patterns
- **WHEN** the agent streams text containing simulated sensitive information such as an email address
- **THEN** the system SHALL replace the matching text with a redact placeholder in the output stream.

#### Scenario: Guardrail interrupts on blocked keyword
- **WHEN** a blocked keyword is generated in the token stream
- **THEN** the system SHALL immediately invoke the agent's interrupt method to halt generation and raise an interruption alert.

### Requirement: Parallel Agent Swarm Example
The system SHALL provide a parallel agent coordination example script that multiplexes event streams from multiple agents executing concurrently.

#### Scenario: Concurrent agent execution and stream merging
- **WHEN** multiple agent loops are executed concurrently using asyncio.gather
- **THEN** the system SHALL interleave their respective text delta streams in the output, prefixed with each agent's identifier.

### Requirement: Self-Healing Coder Example
The system SHALL provide a self-healing developer agent example script where code execution results are fed back to the agent to dynamically repair errors.

#### Scenario: Dynamic repair of python exceptions
- **WHEN** code executed by the agent's tool returns a python exception traceback
- **THEN** the system SHALL feed the traceback context back to the agent as a tool execution output, allowing the agent to modify the code and retry.

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

