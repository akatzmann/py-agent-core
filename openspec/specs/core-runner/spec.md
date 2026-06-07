# core-runner Specification

## Purpose
TBD - created by archiving change system. Update Purpose after archive.
## Requirements
### Requirement: Async Execution Loop
The system SHALL run an asynchronous execution loop that manages the conversation flow of system prompt, user prompt, LLM completion, and tool execution, supporting both a low-level functional stream (`agent_loop`) and a high-level stateful `Agent` wrapper class.

#### Scenario: Execution without tool calls
- **WHEN** the runner executes with a prompt and no tools registered
- **THEN** it SHALL stream granular event dictionaries (`agent_start`, `turn_start`, `message_start`, `message_update`, `message_end`, `turn_end`, `agent_end`) wrapping the LLM completion.

#### Scenario: Execution with tool calls
- **WHEN** the runner executes with a prompt and registered tools, and the LLM requests tool calls
- **THEN** it SHALL yield `tool_execution_start` and `tool_execution_end` events, execute the tool calls, feed the outputs back into the conversation history, and continue the execution loop.

### Requirement: Cooperative Interruption
The system SHALL support cooperative interruption during both token streaming and tool execution phases by supporting an `abort()` method on the high-level `Agent` class and a cancellation signal in the low-level loop.

#### Scenario: Interrupted during token streaming
- **WHEN** the abort signal or interrupt method is invoked while the runner is consuming LLM streaming tokens
- **THEN** the runner SHALL close the underlying response stream immediately, yield `interrupted`, and terminate execution.

#### Scenario: Interrupted before tool execution
- **WHEN** the abort signal is set after a tool call is parsed but before execution begins
- **THEN** the runner SHALL bypass execution of the tool, yield `interrupted`, and terminate execution.

### Requirement: Turn Transition Controls
The system SHALL support dynamic turn transition hooks (`prepare_next_turn` and `should_stop_after_turn`) to customize configuration or stop execution between execution turns.

#### Scenario: Configure next turn
- **WHEN** `prepare_next_turn` is defined and returns a turn update
- **THEN** the system SHALL apply the updated model, reasoning, or context settings to the next LLM call.

#### Scenario: Stop after turn
- **WHEN** `should_stop_after_turn` returns true
- **THEN** the system SHALL immediately terminate the run and yield `agent_end` before starting another turn.

