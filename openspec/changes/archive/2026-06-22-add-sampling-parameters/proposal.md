## Why

Currently, the library's backend adapters and example scripts do not support passing sampling parameters like `temperature` or `top_p`. Adding this configuration at the backend initialization layer provides users with standard generation control in an architecturally decoupled way.

## What Changes

- Update `BaseBackend` abstract base class and concrete backend implementations (`OpenAIBackend`, `OllamaBackend`, `AzureOpenAIBackend`) to accept `temperature` and `top_p` in their constructors.
- Pass these options down through the respective SDK chat/streaming calls, ensuring appropriate default values or fallback behavior.
- Adapt the example CLI argument utility (`examples/utils.py`) to parse `--temperature` and `--top-p` and pass them to the selected backend.
- Update documentation and examples to show how to use these new options.

## Capabilities

### New Capabilities

<!-- None -->

### Modified Capabilities

- `llm-backends`: Backend adapters must accept and apply `temperature` and `top_p` sampling parameters.
- `example-cli-args`: The example runner CLI argument utility must support parsing `--temperature` and `--top-p`.

## Impact

- Modifies `py_agent_core/backends/base.py`, `py_agent_core/backends/openai.py`, `py_agent_core/backends/ollama.py`, and `py_agent_core/backends/azure_openai.py`.
- Modifies `examples/utils.py`.
- Modifies `README.md`.
