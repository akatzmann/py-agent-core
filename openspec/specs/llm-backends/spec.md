# llm-backends Specification

## Purpose
TBD - created by archiving change system. Update Purpose after archive.
## Requirements
### Requirement: Unified Backend Interface
The system SHALL define a common asynchronous interface or abstract base class for LLM client wrappers, ensuring that the `PyAgent` loop can interact with any model provider interchangeably.

#### Scenario: Streaming via unified interface
- **WHEN** the agent loop invokes the unified interface's streaming method with messages and options
- **THEN** it SHALL return an async iterator yielding text chunks, thinking trace chunks, or tool invocation structures in a provider-agnostic format.

### Requirement: AzureOpenAI Adapter
The system SHALL implement a concrete client adapter that integrates with the Azure OpenAI API using the official `openai` Python SDK.

#### Scenario: Azure streaming connection
- **WHEN** a completion request is sent to the AzureOpenAI adapter
- **THEN** it SHALL request a streaming chat completion from the configured Azure OpenAI endpoint and yield standard text and tool-call deltas.

#### Scenario: Azure reasoning effort mapping
- **WHEN** a completion request is sent to the AzureOpenAI adapter with a thinking level configuration and the model supports reasoning effort
- **THEN** the adapter SHALL pass the mapped `reasoning_effort` parameter to the underlying OpenAI API.

### Requirement: OpenAI API Adapter
The system SHALL implement a concrete client adapter that integrates with standard OpenAI API endpoints using the official `openai` Python SDK.

#### Scenario: OpenAI streaming connection
- **WHEN** a completion request is sent to the OpenAI adapter
- **THEN** it SHALL request a streaming chat completion from the configured OpenAI API and yield standard text and tool-call deltas.

#### Scenario: OpenAI reasoning effort mapping
- **WHEN** a completion request is sent to the OpenAI adapter with a thinking level configuration and the model supports reasoning effort
- **THEN** the adapter SHALL pass the mapped `reasoning_effort` parameter to the underlying OpenAI API.

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

### Requirement: DummyBackend Adapter
The system SHALL implement a mock client adapter that generates offline Lorem Ipsum responses without making network requests.

#### Scenario: Simulate offline generation
- **WHEN** a completion request is sent to the DummyBackend adapter
- **THEN** it SHALL generate a stream of Lorem Ipsum text chunks with configurable delay and yield them, simulating standard completion streaming.

### Requirement: Fallback for Unsupported Thinking
The system SHALL log a warning exactly once and gracefully fall back and retry executing without thinking options when a model provider or specific model does not support thinking/reasoning.

#### Scenario: Fallback warning for unsupported models
- **WHEN** a completion request fails due to unsupported thinking parameters (`reasoning_effort` or `think`)
- **THEN** the backend adapter SHALL emit a warning exactly once, cache the unsupported capability at the class level, and automatically retry the request without those parameters.

### Requirement: Sampling Parameters Support
The unified backend interface and concrete adapters (OpenAIBackend, OllamaBackend, AzureOpenAIBackend) SHALL support configuring sampling parameters, specifically `temperature` and `top_p`, during initialization.

#### Scenario: Initialize backend with sampling parameters
- **WHEN** a backend is initialized with `temperature` and `top_p` values
- **THEN** it SHALL store these parameters as instance defaults and apply them to subsequent completion requests.

#### Scenario: Pass sampling parameters to Ollama client
- **WHEN** OllamaBackend generates a stream
- **THEN** it SHALL pass the configured `temperature` and `top_p` inside the `options` dictionary to the Ollama client call.

#### Scenario: Pass sampling parameters to OpenAI client
- **WHEN** OpenAIBackend or AzureOpenAIBackend generates a stream
- **THEN** it SHALL pass the configured `temperature` and `top_p` as parameters in the chat completion request.

### Requirement: Backend Explicit Configuration Overrides
The OpenAI, AzureOpenAI, and Ollama adapters SHALL accept constructor parameters `supports_reasoning` and `supports_sampling` to allow explicit configuration of capabilities and bypass dynamic runtime probing.

#### Scenario: Instantiate backend with overrides
- **WHEN** the OpenAI backend is instantiated with `supports_reasoning=True` and `supports_sampling=False`
- **THEN** it SHALL respect these overrides, passing `reasoning_effort` and omitting `temperature` and `top_p` on all completion requests.

### Requirement: Fallback for Unsupported Sampling Parameters
The system SHALL log a warning exactly once and gracefully fall back and retry without sampling parameters (`temperature` and `top_p`) when a model does not support them.

#### Scenario: Fallback warning for unsupported sampling parameters
- **WHEN** a completion request fails due to unsupported sampling parameters (`temperature` or `top_p`)
- **THEN** the backend adapter SHALL emit a warning exactly once, cache the unsupported capability at the class level, and automatically retry the request without those parameters.

