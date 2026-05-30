## MODIFIED Requirements

### Requirement: Ollama Adapter
The system SHALL implement a concrete client adapter that integrates with local Ollama service instances using the official `ollama` Python SDK or direct HTTP requests.

#### Scenario: Ollama streaming connection
- **WHEN** a completion request is sent to the Ollama adapter
- **THEN** it SHALL request a streaming chat completion from the configured Ollama API and yield text and tool-call deltas.

#### Scenario: Robust argument parsing
- **WHEN** the message history contains tool calls with non-dictionary arguments
- **THEN** the adapter SHALL coerce them to a valid dictionary structure before passing them to the Ollama client to prevent Pydantic validation crashes.
