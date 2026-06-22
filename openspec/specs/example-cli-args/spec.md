# example-cli-args Specification

## Purpose
TBD - created by archiving change example-model-start. Update Purpose after archive.
## Requirements
### Requirement: Command Line Backend Parsing
The system SHALL parse command-line arguments to configure and instantiate the requested model backend for the example scripts dynamically.

#### Scenario: Parse default backend
- **WHEN** an example runner script is executed without any arguments
- **THEN** the system SHALL default to instantiating `DummyBackend` for offline operation.

#### Scenario: Parse Ollama backend
- **WHEN** an example runner script is executed with `--backend ollama`, `--model qwen`, and `--endpoint http://host.containers.internal:11434`
- **THEN** the system SHALL instantiate `OllamaBackend` targeting the specified Ollama endpoint and model.

#### Scenario: Parse Azure OpenAI backend
- **WHEN** an example runner script is executed with `--backend azure`, `--model gpt-4`, `--endpoint http://azure-endpoint`, and `--api-key my-key`
- **THEN** the system SHALL instantiate `AzureOpenAIBackend` configured with the specified endpoint, model deployment, and authentication key.

### Requirement: Command Line Sampling Params Parsing
The system SHALL parse command-line arguments to configure sampling parameters like `temperature` and `top_p` for the backend wrapper.

#### Scenario: Parse custom temperature and top_p
- **WHEN** an example runner script is executed with `--temperature 0.7` and `--top-p 0.9`
- **THEN** the system SHALL instantiate the chosen backend with those configured values.


