## MODIFIED Requirements

### Requirement: Ollama Adapter
The system SHALL implement a concrete client adapter that integrates with local Ollama service instances using the official `ollama` Python SDK or direct HTTP requests.

#### Scenario: Ollama streaming connection
- **WHEN** a completion request is sent to the Ollama adapter
- **THEN** it SHALL request a streaming chat completion from the configured Ollama API and yield text and tool-call deltas.

#### Scenario: Robust argument parsing
- **WHEN** the message history contains tool calls with non-dictionary arguments
- **THEN** the adapter SHALL coerce them to a valid dictionary structure before passing them to the Ollama client to prevent Pydantic validation crashes.

#### Scenario: Ollama thinking trace streaming
- **WHEN** a completion request is sent to the Ollama adapter with thinking enabled and the model supports it
- **THEN** the adapter SHALL request a streaming chat completion with the `think` option enabled, yield thinking deltas in `BackendChunk.thinking`, and sanitize the assistant messages in history by removing the `thinking` key before making the call.

#### Scenario: Stable tool indexing and delta tracking for sequential streams
- **WHEN** multiple tool calls without IDs are streamed from Ollama sequentially across separate single-item chunks
- **THEN** the adapter SHALL match each incoming tool call against the sequence history using call names and argument prefixes, assigning unique stable indices and calculating correct argument deltas to prevent concatenation errors.
