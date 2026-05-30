## Context

When the `PyAgent` loop calls `OllamaBackend.generate_stream`, the history of messages is parsed and sent to the Ollama Python SDK. If the history contains a previous tool call where the model generated arguments as anything other than a dictionary (e.g. a JSON list like `["/path1", "/path2"]`, a primitive value, or a malformed JSON string that fails to decode), the SDK raises a `pydantic.ValidationError` because it enforces that the arguments field must be a `Mapping[str, Any]`. This error propagates as an unhandled exception, crashing the agent run loop and making recovery impossible.

## Goals / Non-Goals

**Goals:**
- Prevent the Ollama SDK from raising `ValidationError` when formatting previously generated tool calls.
- Coerce non-dictionary tool call arguments into a valid dictionary structure before passing them to the Ollama client.
- Ensure that invalid tool call arguments are still routed through the tool execution phase, raising a clean standard error (such as a `TypeError`) that can be fed back to the model as tool execution output.

**Non-Goals:**
- Modifying other backends (like Azure OpenAI), which are unaffected and need to retain their existing message format (since OpenAI API expects `arguments` as a string in the message history).
- Modifying the core `PyAgent` message formatting/storing logic (to keep the framework backend-agnostic and avoid breaking OpenAI).

## Decisions

### Decision 1: Perform translation and coercion in the Ollama Adapter layer
We will perform the sanitization of `tool_calls` arguments inside `py_agent_core/backends/ollama.py` during message serialization.
- *Rationale*: Since the Pydantic ValidationError is a restriction specific to the Ollama client SDK, handling it in the adapter layer isolates the workaround, preventing changes to the generic agent history or other backend adapters.
- *Alternative Considered*: Modifying `agent.py` to always parse tool call arguments into dictionaries. This was rejected because the OpenAI API requires the arguments to be a string in history; changing it globally would break the Azure OpenAI backend.

### Decision 2: Fallback to a dictionary wrapper for invalid arguments
If the arguments string fails to decode, or decodes to a non-dictionary type (e.g., a list or a string), we will wrap the value inside a dictionary with a dummy key: `{"invalid_arguments": args}`.
- *Rationale*: This guarantees that the type sent to the Ollama SDK is a dictionary, satisfying Pydantic validation. During execution, calling the tool function with this keyword argument will raise a `TypeError` (e.g. unexpected keyword argument 'invalid_arguments'), which behaves exactly like an argument validation error, returning the error message to the LLM so it can learn and correct itself.
- *Alternative Considered*: Throwing away the arguments and passing an empty dictionary `{}`. This was rejected because the model would not receive any context about its invalid arguments, making it harder for it to understand why the tool failed.

## Risks / Trade-offs

- **Risk**: The model could repeatedly output the same invalid arguments format.
  - *Mitigation*: Since the tool execution fails with a descriptive `TypeError` containing the unexpected key name (`invalid_arguments`), the model is prompted with the error context, enabling it to correct its tool call.
