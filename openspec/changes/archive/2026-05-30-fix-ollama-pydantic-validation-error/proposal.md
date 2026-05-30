## Why

When using the Ollama backend, if the model generates tool calls with arguments that are not formatted as a valid JSON dictionary (e.g., a JSON list or invalid JSON), the Ollama Python SDK raises a Pydantic `ValidationError`. Because the agent loop does not handle this, the execution loop crashes completely. The model is unable to recover from its error since the invalid tool call remains in the history and triggers the validation error on every subsequent turn.

## What Changes

- Modify the Ollama backend adapter to intercept and safely coerce the tool call arguments into a valid dictionary format (mapping any invalid formats or decode failures to a fallback `{"invalid_arguments": args}` structure).
- Ensure that the Ollama client request never receives non-dictionary arguments, preventing Pydantic `ValidationError` crashes.
- Allow the invalid argument formatting error to propagate naturally through the agent's tool execution phase as a standard Python `TypeError`, which is fed back as an error message tool output to allow the model to dynamically correct its mistake and recover on the next turn.

## Capabilities

### New Capabilities

### Modified Capabilities
- `llm-backends`: Add requirement for the Ollama adapter to robustly handle invalid or non-dictionary tool call arguments without crashing.

## Impact

- Affected code: `py_agent_core/backends/ollama.py`
- Dependencies: `ollama` SDK (Pydantic interaction)
- Systems: Ollama backend integration
