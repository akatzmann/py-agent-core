## Context

In `OllamaBackend.generate_stream`, when a local Ollama model returns tool calls, the API doesn't guarantee a stable unique `id` for each tool call. To handle this, the adapter previously generated fallback IDs like `fallback_{idx}_{func_name}` where `idx` is the index of the tool call in the current chunk's `tool_calls` list.
However, when Ollama streams tool calls sequentially, it yields chunks containing only the *currently active* tool call delta (a list of length 1). This causes `idx` to evaluate to `0` for all sequential tool calls.
Because all sequential tool calls map to `fallback_0_execute_command`, their arguments get concatenated into a single malformed JSON string, leading to syntax/execution failures in the user's terminal.

## Goals / Non-Goals

**Goals:**
- Implement a robust matching algorithm in `OllamaBackend.generate_stream` to assign stable indices (`0`, `1`, `2`, etc.) to sequentially streamed tool calls without IDs.
- Correctly calculate argument deltas for sequentially streamed tool calls.
- Support both cumulative tool call lists and single-item sequential streams.

**Non-Goals:**
- Rewriting downstream JSON parsing in `tool.py` or the `execute_command` logic.
- Adding complex multi-turn state inside the backend (tracking state must be stream-local within the lifecycle of `generate_stream`).

## Decisions

### 1. Maintain a Stream-Local List of Known Tool Calls
- **Decision**: Keep a local list `known_tool_calls = []` inside the `generate_stream` execution generator to track unique tool calls seen so far during the current completion turn.
- **Rationale**: This lets us cross-reference incoming tool calls without IDs against previous chunks to see if they are continuations of the last seen tool call or represent a new tool call.
- **Alternative Considered**: Modifying the agent loop to handle concatenated JSON strings. Rejected because it violates tool calling schemas, breaks fine-grained user confirmation controls, and leaks adapter issues downstream.

### 2. Match Sequential Calls by Name and Argument Prefix
- **Decision**: A tool call in a single-item list chunk matches the last known tool call if and only if the function name matches and the current arguments string starts with the last call's accumulated arguments.
- **Rationale**: Since LLMs output arguments sequentially (growing character by character), a continuation will always start with the previously accumulated string. A new tool call will start over (either with a different name or a clean/empty argument string), causing `startswith` to return `False`, which allows us to increment the index safely.

## Risks / Trade-offs

- **Risk**: A model calls the exact same tool with the exact same arguments twice in a row, and the second call starts immediately after the first.
- **Mitigation**: When the second call starts, its arguments will initially be empty or a partial prefix (e.g. `{"c"`). Since it does not match the fully completed arguments of the first call, `startswith` will evaluate to `False`, and it will be correctly assigned the next index.
