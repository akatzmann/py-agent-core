## Context

`py-agent-core` provides `OpenAIBackend` and `AzureOpenAIBackend` adapters that communicate with OpenAI and Azure OpenAI endpoints via `/v1/chat/completions`. See [proposal.md](proposal.md) for motivation.

When reasoning models (such as `gpt-6.1-sol` or `o3-mini`) are queried with function tools via `/v1/chat/completions`, OpenAI requires `reasoning_effort` to be explicitly set to `"none"`. Omitting the parameter causes server-side default reasoning to activate, resulting in an HTTP 400 `BadRequestError`. Furthermore, the current exception handler in both backends only activates when `use_reasoning` is `True` and uses `kwargs.pop("reasoning_effort")`, causing retry failures.

## Goals / Non-Goals

**Goals:**
- Gracefully handle `BadRequestError` from OpenAI/Azure OpenAI when function tools conflict with reasoning effort on `/v1/chat/completions`.
- Support both explicit thinking (`thinking_level != "off"`) and server-default thinking (`thinking_level == "off"`).
- Cache models requiring `reasoning_effort="none"` for tool calls across the session to avoid duplicate failed round-trips.
- Log an informative warning when reasoning effort is forced to `"none"`.
- Upgrade `openai` SDK in the local `.venv` and provide unit tests covering the new fallback paths.

**Non-Goals:**
- Implementing the `/v1/responses` API endpoint (reserved for future work).
- Modifying Ollama or mock backend implementations.

## Decisions

### Decision 1: Class-level cache `_models_requiring_reasoning_none`
* **Choice**: Add `_models_requiring_reasoning_none = set()` to `OpenAIBackend` and `AzureOpenAIBackend`.
* **Rationale**: In a multi-turn agent task, once a model reports that tools require `reasoning_effort="none"`, all subsequent tool-bearing calls in the same process should proactively pass `reasoning_effort="none"`, saving unnecessary 400 error round-trips.
* **Alternative considered**: Reactive-only handling on each completion. Rejected because it wastes latency and API quota on avoidable error retries.

### Decision 2: Upfront assignment when tools are present
* **Choice**: When building `kwargs` for a completion:
  ```python
  if tools and self.model in self._models_requiring_reasoning_none:
      kwargs["reasoning_effort"] = "none"
  ```
  If the model is in `_models_requiring_reasoning_none` and tools are present, `reasoning_effort` is set to `"none"` upfront and `thinking_level` mapping is skipped.

### Decision 3: Differentiate "unsupported parameter" vs "tools require 'none'"
* **Choice**: In the `BadRequestError` handler:
  1. If `"reasoning_effort"` is in `err_msg` and (`"none"` in err_msg or `"Function tools"` in err_msg or `"tool"` in err_msg):
     - Treat as tool-reasoning incompatibility.
     - Add `self.model` to `self._models_requiring_reasoning_none`.
     - Set `kwargs["reasoning_effort"] = "none"`.
     - Log a warning that reasoning effort is set to `"none"` to allow tool execution.
     - Retry immediately.
  2. Else if `use_reasoning` and `"reasoning_effort"` in `err_msg`:
     - Treat as model having no support for `reasoning_effort` at all (e.g., `gpt-4o`).
     - Add `self.model` to `self._unsupported_reasoning_models`.
     - Pop `kwargs["reasoning_effort"]`.
     - Log a warning and retry.
* **Rationale**: Removes the restrictive `if use_reasoning` prerequisite for tool-conflict errors, fixing crashes when `thinking_level == "off"`.

## Risks / Trade-offs

- **[Risk] Model runs tool-calling turns without reasoning**:
  ↳ *Mitigation*: This is an unavoidable restriction of `/v1/chat/completions`. Graceful fallback allows tool execution to succeed rather than crashing the agent loop. A clear `logger.warning` is emitted.
- **[Risk] Error message text differences across API versions or gateways**:
  ↳ *Mitigation*: The error check inspects `"reasoning_effort"` in combination with `"none"` or `"tool"`, or when `tools` are present in `kwargs`.
