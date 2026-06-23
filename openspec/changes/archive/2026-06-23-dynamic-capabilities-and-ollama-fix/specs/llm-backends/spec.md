## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Fallback for Unsupported Thinking
The system SHALL log a warning exactly once and gracefully fall back and retry executing without thinking options when a model provider or specific model does not support thinking/reasoning.

#### Scenario: Fallback warning for unsupported models
- **WHEN** a completion request fails due to unsupported thinking parameters (`reasoning_effort` or `think`)
- **THEN** the backend adapter SHALL emit a warning exactly once, cache the unsupported capability at the class level, and automatically retry the request without those parameters.
