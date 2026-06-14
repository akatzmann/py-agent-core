## Why

The current implementation of `py-agent-core` lacks support for enabling, disabling, and streaming reasoning/thinking processes from model providers like Ollama (supporting models like DeepSeek-R1 and Qwen3) and Azure OpenAI/OpenAI (supporting models like o1 and o3-mini). This prevents developers from leveraging advanced chain-of-thought capabilities or controlling reasoning latency and cost. 

Adding native model thinking support ensures feature parity with the TypeScript `@earendil-works/pi-agent-core` runtime, which defines standard `ThinkingLevel` settings.

## What Changes

- **Backend Configuration Options:** Modify the unified backend interface (`BaseBackend.generate_stream`) to accept a generic `options` dictionary for provider-agnostic parameters.
- **Provider-Agnostic Thinking Config:** Support mapping a unified `thinking_level` (`"off"`, `"low"`, `"medium"`, `"high"`) parameter to provider-specific APIs (`think` for Ollama, `reasoning_effort` for OpenAI).
- **Separate Streaming Channel for Reasoning:** Extend `BackendChunk` to support a dedicated `thinking` string field, separating reasoning traces from final generated content.
- **Resilient Fallbacks:** Fall back gracefully with developer warnings if a model or backend does not support thinking.
- **Agent Loop and Event Tracking:** Update `agent_loop.py` and the state orchestrator to pass the configuration, accumulate reasoning traces in assistant messages, and emit a stream of reasoning updates (e.g. `thinking_delta`).

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `llm-backends`: Extend the unified backend interface signature to accept options and specify how concrete adapters handle, translate, and stream thinking/reasoning parameters and traces.
- `core-runner`: Update the agent execution runner to propagate thinking configurations to backends, accumulate reasoning traces in message history, and emit reasoning-specific stream updates.

## Impact

- **APIs:** Backward-compatible signatures for `BaseBackend.generate_stream`. New `thinking` property on `BackendChunk`.
- **Event Streams:** New `assistant_message_event` type `thinking_delta` emitted by `Agent.prompt_stream`.
- **State:** `AgentState` starts actively propagating `thinking_level` to the runtime loop.
- **Adapters:** Updates to `OllamaBackend`, `AzureOpenAIBackend`, and `DummyBackend` to support thinking capabilities and options mapping.
