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

