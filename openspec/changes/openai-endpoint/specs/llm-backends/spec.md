## ADDED Requirements

### Requirement: OpenAI API Adapter
The system SHALL implement a concrete client adapter that integrates with standard OpenAI API endpoints using the official `openai` Python SDK.

#### Scenario: OpenAI streaming connection
- **WHEN** a completion request is sent to the OpenAI adapter
- **THEN** it SHALL request a streaming chat completion from the configured OpenAI API and yield standard text and tool-call deltas.

#### Scenario: OpenAI reasoning effort mapping
- **WHEN** a completion request is sent to the OpenAI adapter with a thinking level configuration and the model supports reasoning effort
- **THEN** the adapter SHALL pass the mapped `reasoning_effort` parameter to the underlying OpenAI API.
