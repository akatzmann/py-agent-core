## Why

Currently, the project contains backends for AzureOpenAI, Ollama, and Dummy, but lacks support for standard OpenAI API endpoints. A native OpenAI backend is highly requested and is the most widely supported integration for LLM solutions.

## What Changes

- Implement a new standard `OpenAIBackend` class in a new module `py_agent_core/backends/openai.py` that interfaces with standard OpenAI API endpoints using the official `openai` Python SDK.
- Export `OpenAIBackend` in `py_agent_core/backends/__init__.py`.
- Update package specifications to formally define the new standard OpenAI API backend requirements.

## Capabilities

### New Capabilities

<!-- None -->

### Modified Capabilities

- `llm-backends`: Introduce a requirement for the standard OpenAI API backend adapter, specifying the streaming behavior and reasoning/thinking parameter mapping.

## Impact

- Adds `py_agent_core/backends/openai.py`.
- Modifies `py_agent_core/backends/__init__.py`.
- Modifies `openspec/specs/llm-backends/spec.md` (via a delta spec or direct update as part of the openspec workflow).
