## ADDED Requirements

### Requirement: Fallback for Unsupported Thinking
The system SHALL log a warning and gracefully fall back to executing without thinking options when a model provider or specific model does not support thinking/reasoning.

#### Scenario: Fallback warning for unsupported models
- **WHEN** a backend is invoked with a thinking level configuration but the model does not support reasoning
- **THEN** it SHALL emit a warning and execute the completion request without the thinking parameters.

## MODIFIED Requirements

### Requirement: Unified Backend Interface
The system SHALL define a common asynchronous interface or abstract base class for LLM client wrappers, ensuring that the `PyAgent` loop can interact with any model provider interchangeably.

#### Scenario: Streaming via unified interface
- **WHEN** the agent loop invokes the unified interface's streaming method with messages and options
- **THEN** it SHALL return an async iterator yielding text chunks, thinking trace chunks, or tool invocation structures in a provider-agnostic format.

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

### Requirement: AzureOpenAI Adapter
The system SHALL implement a concrete client adapter that integrates with the Azure OpenAI API using the official `openai` Python SDK.

#### Scenario: Azure streaming connection
- **WHEN** a completion request is sent to the AzureOpenAI adapter
- **THEN** it SHALL request a streaming chat completion from the configured Azure OpenAI endpoint and yield standard text and tool-call deltas.

#### Scenario: Azure reasoning effort mapping
- **WHEN** a completion request is sent to the AzureOpenAI adapter with a thinking level configuration and the model supports reasoning effort
- **THEN** the adapter SHALL pass the mapped `reasoning_effort` parameter to the underlying OpenAI API.
