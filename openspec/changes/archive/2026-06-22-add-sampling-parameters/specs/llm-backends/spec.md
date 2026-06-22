## ADDED Requirements

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
