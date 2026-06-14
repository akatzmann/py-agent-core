## Context

Historically, the orchestrator and backends in `py-agent-core` only expected a linear stream of text or structured tool calls. Newer models like DeepSeek R1 and OpenAI o1/o3-mini introduce a native multi-channel response format where a model first produces internal reasoning ("thinking") before emitting the final content. 
To integrate these models without leaking raw CoT tags into the chat transcript or breaking tool call argument parsing, the runtime needs unified abstractions for configuring, propagating, and streaming thinking traces separately.

## Goals / Non-Goals

**Goals:**
- Enable standard thinking configurations (`thinking_level` like `"off"`, `"low"`, `"medium"`, `"high"`) on `Agent` and `AgentState`.
- Pass these options seamlessly to `BaseBackend.generate_stream` in a backward-compatible manner.
- Separate reasoning chunks from standard text output in concrete backend adapters.
- Stream reasoning tokens to listeners via a dedicated event type/payload.
- Gracefully fall back to standard execution if the target model or provider lacks reasoning support.

**Non-Goals:**
- Backwards-compatible support for `PyAgent.run_loop` or `LegacyAgentEvent` yielding thinking traces.
- Custom client-side parsing of text content to extract `<think>` tags for older models that do not support native reasoning structures in their API.

## Decisions

### 1. Unified `options` dictionary in `BaseBackend.generate_stream`
- **Choice:** Add `options: Optional[Dict[str, Any]] = None` keyword parameter to `BaseBackend.generate_stream`.
- **Rationale:** Rather than adding explicit parameters like `thinking_level`, a generic `options` dictionary maintains signature backward compatibility and allows easy expansion to support properties like `temperature`, `max_tokens`, or `user` in the future without signature modification.
- **Alternatives Considered:** Adding `thinking_level: Optional[str] = None` directly. This was rejected because it forces signature updates whenever new options are introduced.

### 2. Multi-Channel `BackendChunk` abstraction
- **Choice:** Add `thinking: Optional[str] = None` to `BackendChunk`.
- **Rationale:** Ollama emits thinking and content in separate fields. Yielding them on distinct fields in `BackendChunk` lets the runner process them distinctly.
- **Alternatives Considered:** Yielding thinking tokens as standard text but prefixed/wrapped. This was rejected as it forces downstreams to parse content.

### 3. Graceful Warning Fallbacks
- **Choice:** Implement logger-based warnings in concrete adapters when reasoning is requested but unsupported by the model.
- **Rationale:** Keeps the agent runner running when switching between models, while still informing the developer that their request to enable/disable reasoning could not be honored.
- **Alternatives Considered:** Raising an exception (too disruptive) or failing silently (difficult to debug).

### 4. Message History Sanitation in Adapters
- **Choice:** Concrete adapters (like `OllamaBackend`) will format the message list sent to the LLM client by deleting the `thinking` key from assistant messages in context.
- **Rationale:** Prevents context window bloat and potential model confusion by keeping thinking traces out of context history.

## Risks / Trade-offs

- **[Risk]** Ollama API might change chunk structure or fields for thinking.
  - **Mitigation:** Fall back to reading the `content` field if `thinking` is missing, and test with the latest Ollama SDK versions.
- **[Risk]** Certain models may support thinking but only return raw text (e.g., without separate field support in older local models).
  - **Mitigation:** This design explicitly limits scope to native thinking APIs (where thinking is a distinct field/parameter in the provider SDK). If older models are used, their outputs are treated as normal text content.
