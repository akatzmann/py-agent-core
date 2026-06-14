## MODIFIED Requirements

### Requirement: Async Execution Loop
The system SHALL run an asynchronous execution loop that manages the conversation flow of system prompt, user prompt, LLM completion, and tool execution, supporting both a low-level functional stream (`agent_loop`) and a high-level stateful `Agent` wrapper class.

#### Scenario: Execution without tool calls
- **WHEN** the runner executes with a prompt and no tools registered
- **THEN** it SHALL stream granular event dictionaries (`agent_start`, `turn_start`, `message_start`, `message_update`, `message_end`, `turn_end`, `agent_end`) wrapping the LLM completion.

#### Scenario: Execution with tool calls
- **WHEN** the runner executes with a prompt and registered tools, and the LLM requests tool calls
- **THEN** it SHALL yield `tool_execution_start` and `tool_execution_end` events, execute the tool calls, feed the outputs back into the conversation history, and continue the execution loop.

#### Scenario: Execution with model thinking enabled
- **WHEN** the runner executes with model thinking enabled
- **THEN** it SHALL propagate the thinking level, yield `message_update` events of type `thinking_delta`, and accumulate the reasoning trace in the assistant's message dictionary under the `thinking` key.

### Requirement: Turn Transition Controls
The system SHALL support dynamic turn transition hooks (`prepare_next_turn` and `should_stop_after_turn`) to customize configuration or stop execution between execution turns.

#### Scenario: Configure next turn
- **WHEN** `prepare_next_turn` is defined and returns a turn update
- **THEN** the system SHALL apply the updated model, reasoning (including `thinking_level`), or context settings to the next LLM call.

#### Scenario: Stop after turn
- **WHEN** `should_stop_after_turn` returns true
- **THEN** the system SHALL immediately terminate the run and yield `agent_end` before starting another turn.
