## MODIFIED Requirements

### Requirement: Fallback for Unsupported Thinking
The system SHALL log a warning and gracefully fall back and retry executing when a model provider or specific model does not support thinking/reasoning options, or when function tools are incompatible with active reasoning effort on the completion endpoint.

#### Scenario: Fallback warning for unsupported models
- **WHEN** a completion request fails due to unsupported thinking parameters (`reasoning_effort` or `think`)
- **THEN** the backend adapter SHALL emit a warning exactly once, cache the unsupported capability at the class level, and automatically retry the request without those parameters.

#### Scenario: Fallback to reasoning effort none for function tools
- **WHEN** a completion request with function tools fails because the model requires `reasoning_effort` to be set to `'none'` (or does not support function tools with reasoning effort on `/v1/chat/completions`)
- **THEN** the OpenAI or AzureOpenAI backend adapter SHALL log a warning, cache the model requirement at the class level, and automatically retry the request with `reasoning_effort="none"`.

#### Scenario: Fallback when thinking level is off
- **WHEN** a completion request with function tools and default thinking level (`"off"`) fails due to server-side default reasoning rejecting tools
- **THEN** the adapter SHALL intercept the error, log a warning, cache the model requirement, and retry with `reasoning_effort="none"`.
