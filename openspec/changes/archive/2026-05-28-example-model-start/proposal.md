## Why

Currently, the executable examples in the `examples/` directory hardcode the `DummyBackend` adapter and mocked data. To run these examples against live local models (e.g., via Ollama) or enterprise endpoints (e.g., Azure OpenAI), developers need a standardized way to specify backend selection, endpoint URLs, and model names via command-line arguments.

## What Changes

- Create a shared argument parser helper in `examples/utils.py` (or as a helper function).
- Support the following CLI options for all 4 examples:
  - `--backend`: Choose from `dummy`, `ollama`, or `azure` (defaults to `dummy`).
  - `--model`: Specify the LLM model name (e.g., `llama3`, `qwen3-4b-instruct-2507:latest`, `gpt-4o-mini`).
  - `--endpoint`: Configure the endpoint URL (e.g., `http://host.containers.internal:11434` for Ollama).
  - `--api-key`: Provide the API key (for Azure OpenAI).
- Refactor the 4 existing example scripts to use this helper to dynamically instantiate the selected backend, enabling live endpoint testing.

## Capabilities

### New Capabilities
- `example-cli-args`: Dynamic backend configuration for example runners via command-line arguments.

### Modified Capabilities
<!-- None -->

## Impact

- Refactors files in the `examples/` directory.
- No impact on core library files under `py_agent_core/`.
