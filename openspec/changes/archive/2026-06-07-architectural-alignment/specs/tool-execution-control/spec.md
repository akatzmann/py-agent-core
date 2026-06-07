## ADDED Requirements

### Requirement: Parallel Tool Execution
The system SHALL support concurrent tool execution for independent tool calls within the same turn.

#### Scenario: Running multiple tools concurrently
- **WHEN** the agent receives multiple tool calls from the LLM and the execution mode is set to "parallel"
- **THEN** it SHALL execute them concurrently, emitting individual `tool_execution_start` and `tool_execution_end` events as they start and finish, while maintaining final result order matching the LLM's requests.

### Requirement: Tool Interception Hooks
The system SHALL support user-defined hooks (`before_tool_call` and `after_tool_call`) to intercept, preflight, authorize, or post-process tool executions.

#### Scenario: Preflight block tool execution
- **WHEN** a `before_tool_call` hook returns a block result
- **THEN** the system SHALL skip executing the tool and return the block reason to the LLM.

#### Scenario: Post-execution modification
- **WHEN** a `after_tool_call` hook modifies the result or requests early termination
- **THEN** the system SHALL apply those changes to the tool results returned to the LLM and respect the termination signal.
