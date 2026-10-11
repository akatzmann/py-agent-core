## MODIFIED Requirements

### Requirement: AzureOpenAI Adapter
The system SHALL implement a concrete client adapter that integrates with the Azure OpenAI API using the official `openai` Python SDK, supporting both the `/v1/responses` API and legacy chat completions.

#### Scenario: Azure streaming connection
- **WHEN** a completion request is sent to the AzureOpenAI adapter
- **THEN** it SHALL request a streaming response from the configured Azure OpenAI endpoint and yield standard text, thinking trace, and tool-call deltas.

#### Scenario: Azure reasoning effort mapping
- **WHEN** a completion request is sent to the AzureOpenAI adapter with a thinking level configuration and the model supports reasoning effort
- **THEN** the adapter SHALL pass the mapped reasoning configuration to the underlying Azure OpenAI API.

#### Scenario: Azure responses streaming with function tools
- **WHEN** a completion request is sent with function tools and active reasoning configuration targeting the `/v1/responses` endpoint
- **THEN** the adapter SHALL request streaming via `client.responses.create` and yield text, thinking traces, and tool call argument deltas without disabling reasoning effort.

#### Scenario: Runtime protocol fallback for unsupported responses endpoint
- **WHEN** a request in auto mode targets `/v1/responses` on an Azure deployment whose API version or gateway does not support responses (returning 404 or unsupported operation)
- **THEN** the adapter SHALL cache the endpoint capability and fall back to `/v1/chat/completions`.

### Requirement: OpenAI API Adapter
The system SHALL implement a concrete client adapter that integrates with standard OpenAI API endpoints using the official `openai` Python SDK, supporting both the `/v1/responses` API and legacy chat completions.

#### Scenario: OpenAI streaming connection
- **WHEN** a completion request is sent to the OpenAI adapter
- **THEN** it SHALL request a streaming response from the configured OpenAI API and yield standard text, thinking trace, and tool-call deltas.

#### Scenario: OpenAI reasoning effort mapping
- **WHEN** a completion request is sent to the OpenAI adapter with a thinking level configuration and the model supports reasoning effort
- **THEN** the adapter SHALL pass the mapped reasoning configuration to the underlying OpenAI API.

#### Scenario: OpenAI responses streaming with function tools
- **WHEN** a completion request is sent with function tools and active reasoning configuration targeting the `/v1/responses` endpoint
- **THEN** the adapter SHALL request streaming via `client.responses.create` and yield text, thinking traces, and tool call argument deltas without disabling reasoning effort.

#### Scenario: Runtime protocol promotion when chat completions rejects tool reasoning
- **WHEN** a request on `/v1/chat/completions` with function tools fails because the model requires `/v1/responses` or rejects `reasoning_effort='none'`
- **THEN** the adapter SHALL dynamically promote the turn to `/v1/responses`, stream the completion, and cache the requirement.

### Requirement: Backend Explicit Configuration Overrides
The OpenAI, AzureOpenAI, and Ollama adapters SHALL accept constructor parameters `supports_reasoning`, `supports_sampling`, and `api_mode` to allow explicit configuration of capabilities and wire protocol.

#### Scenario: Instantiate backend with overrides
- **WHEN** the OpenAI backend is instantiated with `supports_reasoning=True` and `supports_sampling=False`
- **THEN** it SHALL respect these overrides, passing reasoning configuration and omitting `temperature` and `top_p` on all completion requests.

#### Scenario: Instantiate backend with explicit api_mode
- **WHEN** the backend is instantiated with `api_mode="responses"` or `api_mode="chat_completions"`
- **THEN** it SHALL route completion requests directly to the configured endpoint wire protocol without probing.
