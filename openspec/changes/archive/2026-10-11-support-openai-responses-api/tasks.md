## 1. Message and Tool Conversion for Responses API

- [x] 1.1 Implement message history conversion helper `_convert_messages_for_responses` to extract `instructions` and format input items (user, assistant, tool calls, and tool outputs).
- [x] 1.2 Implement tool definition conversion helper `_convert_tools_for_responses` to format tools for the `/v1/responses` API.

## 2. Responses API Event Streaming

- [x] 2.1 Implement event stream parser mapping `/v1/responses` streaming events (`ResponseTextDeltaEvent`, `ResponseReasoningTextDeltaEvent`, `ResponseFunctionCallArgumentsDeltaEvent`) to `BackendChunk`.
- [x] 2.2 Implement `_generate_stream_responses` in `OpenAIBackend` and `AzureOpenAIBackend` using `client.responses.create(stream=True, ...)`.

## 3. Protocol Negotiation and Configuration

- [x] 3.1 Add `api_mode: Literal["auto", "responses", "chat_completions"] = "auto"` to `OpenAIBackend` and `AzureOpenAIBackend` constructors.
- [x] 3.2 Implement endpoint capability caching to record endpoints that do not support responses or that require responses for tools.
- [x] 3.3 Implement optimistic responses dispatch in `"auto"` mode with graceful fallback to chat completions on 404/405 or unsupported endpoint errors.
- [x] 3.4 Implement dynamic promotion from chat completions to responses when chat completions rejects function tools with active reasoning.

## 4. Testing and Verification

- [x] 4.1 Add unit tests in `tests/test_backend.py` for conversion helpers (`_convert_messages_for_responses` and `_convert_tools_for_responses`).
- [x] 4.2 Add unit tests for `/v1/responses` streaming verifying text deltas, thinking trace chunks, and tool call chunks.
- [x] 4.3 Add unit tests for runtime protocol negotiation: fallback on 404 and promotion on tool-reasoning conflict.
- [x] 4.4 Add unit tests for explicit `api_mode="responses"` and `api_mode="chat_completions"`.
- [x] 4.5 Run pytest test suite to ensure all tests pass with zero regressions.

## 5. Documentation

- [x] 5.1 Update `README.md` documenting `/v1/responses` support, `api_mode` configuration, and runtime protocol negotiation.
