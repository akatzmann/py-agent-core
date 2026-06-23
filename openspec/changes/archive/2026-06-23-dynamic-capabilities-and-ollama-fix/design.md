## Context

The agent backends currently use hardcoded model lists to decide whether to send reasoning and sampling options. This breaks when using newer models, custom Azure deployments, and custom local models. In addition, the Ollama backend's tool chunking logic is buggy because it does not maintain stable indices or compute argument deltas, resulting in syntax errors on parallel tool calls due to duplicated arguments.

## Goals / Non-Goals

**Goals:**
- Eliminate all hardcoded model lists across all backends.
- Allow users to explicitly override reasoning/sampling capabilities in backend constructors.
- Support runtime feature probing: try the parameters and automatically fall back and retry on `BadRequestError`/`ResponseError` from the APIs, logging a warning once and caching the result.
- Fix Ollama tool calling to support stable indexing and argument slicing (deltas).

**Non-Goals:**
- Modifying other adapters (like DummyBackend) which don't communicate with real APIs.
- Modifying the core Agent loop execution logic (all fixes are contained within the backend adapters).

## Decisions

### 1. Unified Constructor Overrides
- **Decision**: Add `supports_reasoning` (and `supports_sampling` for OpenAI/Azure) to the backend class constructors.
- **Rationale**: Gives users complete control to declare model capabilities explicitly, bypass probing, and avoid warning logs entirely.
- **Alternatives considered**: central config file (adds unnecessary complexity to a lightweight Python library).

### 2. Runtime Capability Probing and Retry
- **Decision**: Wrap API creation calls in a `try-except` block. If a request fails with `BadRequestError` (OpenAI/Azure) or `ResponseError` (Ollama) due to unsupported parameters, cache that the model lacks the capability, log a warning once, and retry the request without the failed parameter.
- **Rationale**: Eliminates the need for any static model lists. The retry only happens on the first call for a model, meaning no long-term latency impact.
- **Alternatives considered**: Probing with a lightweight dummy call (e.g. `max_tokens=1`), but this adds network request overhead even for successful calls.

### 3. Class-Level Capability Cache
- **Decision**: Cache unsupported models in class-level sets (e.g., `_unsupported_reasoning_models`).
- **Rationale**: Ensures the cache is shared across all instances of a backend for the lifetime of the process.

### 4. Ollama Tool Arguments Slicing (Delta)
- **Decision**: In `OllamaBackend.generate_stream`, track active tool calls using `tool_call_ids = []` and accumulated yielded arguments using `yielded_arguments = {}`. Yield only the difference (delta) of JSON string arguments compared to previously yielded characters, using stable indices from `tool_call_ids.index(tc_id)`.
- **Rationale**: Correctly maps tool calls across multiple streaming chunks and matches the agent loop's expectation of receiving tool call deltas, resolving argument duplication.

## Risks / Trade-offs

- **Risk**: The first API request to an unsupported model with thinking/sampling enabled will suffer double latency due to the retry.
- **Mitigation**: This only occurs on the first API call per process. Subsequent calls use the class-level cache to bypass the parameter immediately.
- **Risk**: The API error message format might change in the future, preventing string matches for `"reasoning_effort"` or `"temperature"`.
- **Mitigation**: We perform a robust substring match on the exception string. If the error format changes, the first request will fail normally, which acts as a safe default.
