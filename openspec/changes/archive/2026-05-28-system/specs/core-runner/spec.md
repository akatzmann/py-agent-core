## ADDED Requirements

### Requirement: Async Execution Loop
The system SHALL run an asynchronous execution loop that manages the conversation flow of system prompt, user prompt, LLM completion, and automatic tool execution.

#### Scenario: Execution without tool calls
- **WHEN** the runner executes with a prompt and no tools registered
- **THEN** the runner SHALL stream the LLM completion, yielding `text_delta` events, followed by a final `done` event containing the completed text.

#### Scenario: Execution with tool calls
- **WHEN** the runner executes with a prompt and registered tools, and the LLM requests a tool call
- **THEN** the runner SHALL yield `tool_start` and `tool_end` events, execute the tool asynchronously, feed the output back into the conversation history, and continue the execution loop until the LLM returns a final answer.

### Requirement: Cooperative Interruption
The system SHALL support cooperative interruption during both token streaming and tool execution phases by listening to an internal interrupt flag.

#### Scenario: Interrupted during token streaming
- **WHEN** the interrupt flag is set while the runner is consuming LLM streaming tokens
- **THEN** the runner SHALL close the underlying response stream immediately and yield an `interrupted` event.

#### Scenario: Interrupted before tool execution
- **WHEN** the interrupt flag is set after a tool call is parsed but before execution begins
- **THEN** the runner SHALL bypass execution of the tool and yield an `interrupted` event.
