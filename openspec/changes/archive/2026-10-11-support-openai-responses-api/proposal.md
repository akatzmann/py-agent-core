## Why

Reasoning-native models (such as `gpt-6.1-sol` and other frontier models) strictly enforce reasoning tokens (`reasoning_effort` cannot be set to `"none"`). Because `/v1/chat/completions` fundamentally forbids function calling while reasoning is active, these models cannot execute tools on the chat completions endpoint. 

OpenAI's official API for combining reasoning models with function tools is `/v1/responses`. To avoid locking `py-agent-core` out of modern and future frontier model releases while preserving full backward compatibility with legacy models and proxies, `py-agent-core` must support `/v1/responses` through runtime capability negotiation—without fragile guessing based on arbitrary model or deployment names.

## What Changes

- **Support `/v1/responses` Endpoint**: Implement streaming client communication via `client.responses.create(stream=True, ...)` for both `OpenAIBackend` and `AzureOpenAIBackend`.
- **Dual-Protocol Support**: Support both `/v1/responses` and legacy `/v1/chat/completions`, controlled by `api_mode` (`"auto"`, `"responses"`, `"chat_completions"`).
- **Runtime Capability Negotiation (No Model-Name Guessing)**: In `"auto"` mode, determine protocol behavior via server response codes rather than string-matching model names:
  - Optimistically attempt `/v1/responses`; if the gateway returns HTTP 404 or unsupported operation (older gateway or API version), transparently fall back to `/v1/chat/completions` and cache the endpoint capability.
  - If a request on `/v1/chat/completions` fails because tools cannot run with reasoning effort, dynamically promote the turn to `/v1/responses`.
- **Event Translation**: Map `/v1/responses` stream events (`ResponseTextDeltaEvent`, `ResponseReasoningTextDeltaEvent`, `ResponseFunctionCallArgumentsDeltaEvent`, etc.) into `py-agent-core`'s unified `BackendChunk`.
- **Message & Tool Schema Mapping**: Provide bijective translation between standard agent history and the `/v1/responses` item structure (`instructions`, `input`, and tool definitions).

## Capabilities

### New Capabilities

<!-- None -->

### Modified Capabilities

- `llm-backends`: Extend the OpenAI and AzureOpenAI backend requirements to support `/v1/responses` streaming alongside `/v1/chat/completions`, with runtime capability negotiation and explicit `api_mode` configuration.

## Impact

- **Affected code**: `py_agent_core/backends/openai.py`, `py_agent_core/backends/azure_openai.py`, and `tests/test_backend.py`.
- **APIs**: Adds `api_mode: Literal["auto", "responses", "chat_completions"] = "auto"` to `OpenAIBackend` and `AzureOpenAIBackend`. Existing parameters and interfaces remain backward-compatible.
- **Dependencies**: Uses `openai>=3.28.0` already established in the project.
