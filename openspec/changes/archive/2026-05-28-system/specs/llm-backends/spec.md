## ADDED Requirements

### Requirement: Unified Backend Interface
The system SHALL define a common asynchronous interface or abstract base class for LLM client wrappers, ensuring that the `PyAgent` loop can interact with any model provider interchangeably.

#### Scenario: Streaming via unified interface
- **WHEN** the agent loop invokes the unified interface's streaming method with messages and options
- **THEN** it SHALL return an async iterator yielding text chunks or tool invocation structures in a provider-agnostic format.

### Requirement: AzureOpenAI Adapter
The system SHALL implement a concrete client adapter that integrates with the Azure OpenAI API using the official `openai` Python SDK.

#### Scenario: Azure streaming connection
- **WHEN** a completion request is sent to the AzureOpenAI adapter
- **THEN** it SHALL request a streaming chat completion from the configured Azure OpenAI endpoint and yield standard text and tool-call deltas.

### Requirement: Ollama Adapter
The system SHALL implement a concrete client adapter that integrates with local Ollama service instances using the official `ollama` Python SDK or direct HTTP requests.

#### Scenario: Ollama streaming connection
- **WHEN** a completion request is sent to the Ollama adapter
- **THEN** it SHALL request a streaming chat completion from the configured Ollama API and yield text and tool-call deltas.

### Requirement: DummyBackend Adapter
The system SHALL implement a mock client adapter that generates offline Lorem Ipsum responses without making network requests.

#### Scenario: Simulate offline generation
- **WHEN** a completion request is sent to the DummyBackend adapter
- **THEN** it SHALL generate a stream of Lorem Ipsum text chunks with configurable delay and yield them, simulating standard completion streaming.
