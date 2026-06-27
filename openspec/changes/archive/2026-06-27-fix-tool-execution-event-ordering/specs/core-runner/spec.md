## MODIFIED Requirements

### Requirement: Async Execution Loop
The system SHALL run an asynchronous execution loop that manages the conversation flow of system prompt, user prompt, LLM completion, and tool execution, supporting both a low-level functional stream (`agent_loop`) and a high-level stateful `Agent` wrapper class.

#### Scenario: Execution without tool calls
- **WHEN** the runner executes with a prompt and no tools registered
- **THEN** it SHALL stream granular event dictionaries (`agent_start`, `turn_start`, `message_start`, `message_update`, `message_end`, `turn_end`, `agent_end`) wrapping the LLM completion.

#### Scenario: Execution with tool calls
- **WHEN** the runner executes with a prompt and registered tools, and the LLM requests tool calls
- **THEN** it SHALL yield `tool_execution_start` and `tool_execution_end` events, execute the tool calls, feed the outputs back into the conversation history, and continue the execution loop.

#### Scenario: Streaming rendezvous event delivery
- **WHEN** events are streamed via `Agent.prompt_stream()`
- **THEN** the runner SHALL synchronously acknowledge each emitted event after it is yielded to the downstream consumer iterator, ensuring `tool_execution_start` is yielded before tool execution side-effects begin.

#### Scenario: Backend failure in execution loop
- **WHEN** the LLM backend generation fails or raises an error during execution
- **THEN** it SHALL emit an `error` event and propagate the exception to the caller of `agent_loop` or `Agent.prompt`.

#### Scenario: Backend failure in streaming execution
- **WHEN** the LLM backend generation fails or raises an error during a streaming prompt invocation (`Agent.prompt_stream`)
- **THEN** it SHALL emit an `error` event, yield it, and propagate the exception to the generator's caller.

#### Scenario: Backend failure in legacy wrapper
- **WHEN** backend generation fails when executing via the legacy `PyAgent.run_loop` wrapper
- **THEN** it SHALL yield a legacy `error` event without raising the exception to the caller.

#### Scenario: Execution with model thinking enabled
- **WHEN** the runner executes with model thinking enabled
- **THEN** it SHALL propagate the thinking level, yield `message_update` events of type `thinking_delta`, and accumulate the reasoning trace in the assistant's message dictionary under the `thinking` key.
