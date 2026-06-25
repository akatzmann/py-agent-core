## Why

When local Ollama models (like Qwen) stream tool calls sequentially, they are yielded in separate chunks where each chunk contains only the active tool call delta (a list of length 1). Because the fallback ID logic relies on the transient list index of the chunk (`fallback_{idx}_{name}`), all tool calls collide on index `0`, causing their JSON arguments to concatenate and fail with syntax errors in the terminal bash runner.

## What Changes

- **Ollama Adapter Indexing Fix**: Update `OllamaBackend.generate_stream` to robustly track unique tool calls sequentially across chunks. Instead of relying on the transient position in the current chunk's `tool_calls` list, it will match against a local history of known tool calls by sequence index and arguments delta.
- **Improved Tool Call Stability**: Ensure that multiple tool calls generated during a stream turn get distinct stable indices (`0`, `1`, `2`, etc.) even when yielded sequentially in single-item lists.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `llm-backends`: Update the Ollama adapter scenario to specify that it must correctly yield tool call chunks with stable and unique indices across sequential chunks to prevent arguments concatenation.

## Impact

- `py_agent_core/backends/ollama.py`: Rewrite the tool chunk delta and index generation.
- `tests/test_backend.py`: Add test cases to verify sequential delta streams with colliding list indexes.
