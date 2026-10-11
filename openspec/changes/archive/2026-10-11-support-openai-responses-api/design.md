## Context

`py_agent_core` currently calls `client.chat.completions.create(...)` in `OpenAIBackend` and `AzureOpenAIBackend`. Frontier reasoning models (such as `gpt-6.1-sol` and `o-` series) cannot use function tools on `/v1/chat/completions` because reasoning cannot be disabled with `reasoning_effort="none"`. See [proposal.md](proposal.md) for motivation.

Furthermore, model identifiers in Azure OpenAI and enterprise proxies are arbitrary deployment names (e.g. `agent-runner-prod`), meaning capability decisions must not rely on model name string heuristics.

## Goals / Non-Goals

**Goals:**
- Implement `/v1/responses` streaming in `OpenAIBackend` and `AzureOpenAIBackend`, supporting native reasoning and function tools simultaneously.
- Map `/v1/responses` event streams into unified `BackendChunk` (text deltas, thinking trace deltas, tool call deltas).
- Implement pure capability-based protocol negotiation (Zero Model-Name Guessing):
  - In `api_mode="auto"`, optimistically target `/v1/responses`; fall back to `/v1/chat/completions` if the server returns 404 or unsupported operation.
  - If a `/v1/chat/completions` call fails due to tool-reasoning conflicts, dynamically promote the turn to `/v1/responses`.
  - Cache negotiated protocol per endpoint to avoid repeated probing.
- Support explicit `api_mode: Literal["auto", "responses", "chat_completions"] = "auto"`.

**Non-Goals:**
- Built-in MCP server protocol handling in this change (focus on responses LLM streaming adapter).
- Modifying Ollama or Dummy backends.

## Decisions

### Decision 1: Internal Protocol Delegation within Existing Adapters
* **Choice**: Keep `OpenAIBackend` and `AzureOpenAIBackend` as the primary user-facing classes, implementing internal helpers:
  - `_generate_stream_responses(messages, tools, options, kwargs)`
  - `_generate_stream_chat_completions(clean_messages, tools, options, kwargs)`
* **Rationale**: Maintains 100% backward compatibility for existing code, configuration scripts, and frameworks (like `slash-agent`) while adding the `api_mode` parameter.
* **Alternative considered**: Requiring users to import a completely separate `OpenAIResponsesBackend`. Rejected because it creates fragmentation and forces caller code to choose the backend class manually.

### Decision 2: Zero Model-Name Guessing via Runtime Negotiation
* **Choice**: Never inspect `self.model` string to determine capabilities. Instead:
  1. If `api_mode == "responses"`, always use `/v1/responses`.
  2. If `api_mode == "chat_completions"`, always use `/v1/chat/completions`.
  3. If `api_mode == "auto"`:
     - Check class-level cache: if endpoint is known to not support responses, use chat completions.
     - Otherwise, attempt `/v1/responses`. If the gateway returns `404 Not Found`, `405 Method Not Allowed`, or `BadRequestError` indicating responses is not supported, cache the endpoint in `_unsupported_responses_endpoints` and fall back to chat completions.
     - Conversely, if chat completions is used and fails with a tool-reasoning conflict (`reasoning_effort` incompatible with tools or `unsupported_value` for `"none"`), dynamically promote to `/v1/responses` and cache `_requires_responses_for_tools`.
* **Rationale**: Works seamlessly with arbitrary Azure deployment names and private proxies.

### Decision 3: Event Stream Normalization
* **Choice**: In `_generate_stream_responses`:
  - `ResponseTextDeltaEvent` (or event with `type == "response.text.delta"`): yield `BackendChunk(text=event.delta)`
  - `ResponseReasoningTextDeltaEvent` (or event with `type == "response.reasoning.text.delta"`): yield `BackendChunk(thinking=event.delta)`
  - `ResponseFunctionCallArgumentsDeltaEvent` / `ResponseOutputItemAddedEvent`: accumulate tool calls and yield `BackendChunk(tool_calls=[ToolCallChunk(...)])`.
* **Rationale**: Directly maps into the existing `py-agent-core` event-driven architecture with zero changes required to `agent_loop`.

### Decision 4: History and Tool Conversion
* **Choice**: Provide clean converters:
  - System messages extracted to `instructions: Optional[str]`.
  - User and assistant messages mapped to `{"type": "message", "role": ..., "content": ...}`.
  - Assistant tool calls mapped to `{"type": "function_call", "call_id": id, "name": name, "arguments": args}`.
  - Tool results mapped to `{"type": "function_call_output", "call_id": id, "output": content}`.
  - Tools converted to `{"type": "function", "name": ..., "description": ..., "parameters": ...}`.

## Risks / Trade-offs

- **[Risk] Gateways returning unexpected error schemas**:
  ↳ *Mitigation*: Inspect both standard `openai.APIStatusError` status codes (404, 405) and error message substrings when evaluating protocol support.
- **[Risk] State tracking during streaming tool arguments**:
  ↳ *Mitigation*: Track item output index and call IDs to preserve stable tool call indexing across chunks.
