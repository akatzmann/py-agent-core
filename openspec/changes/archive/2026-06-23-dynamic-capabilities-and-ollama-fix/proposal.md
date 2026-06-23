## Why

Currently, the agent LLM backends rely on static, hardcoded lists of model names to determine if a model supports thinking options (e.g. `reasoning_effort`) or sampling parameters (`temperature`, `top_p`). This is fragile and fails for new models, custom Azure deployments, and custom local models. Additionally, the Ollama tool streaming client causes command execution syntax errors by concatenating multiple tool calls under a single command string because it does not assign stable indexes or compute argument deltas.

## What Changes

- **Modified Capabilities**:
  - Remove all static lists of reasoning models across the LLM backends (OpenAI, Azure, Ollama).
  - Implement explicit overrides (`supports_reasoning` and `supports_sampling`) in the constructors of the backend classes.
  - Implement runtime feature detection and fallback logic: if the API throws a `BadRequestError`/`ResponseError` for reasoning or sampling options, the backend will log a warning once, cache the capability state at the class level, and automatically retry without the unsupported parameters.
  - Fix the Ollama tool stream chunk processing to assign stable, chunk-independent indexes and correctly compute argument deltas to prevent syntax errors during execution.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `llm-backends`: Introduce dynamic parameter probing, fallback, retry mechanism, and constructor overrides for reasoning and sampling options.

## Impact

- `py_agent_core/backends/openai.py`, `py_agent_core/backends/azure_openai.py`, `py_agent_core/backends/ollama.py`: Modifies constructors and `generate_stream` methods.
- `tests/test_backend.py`: Updates existing backend tests to mock realistic BadRequestError scenarios and verifies fallback retries.
