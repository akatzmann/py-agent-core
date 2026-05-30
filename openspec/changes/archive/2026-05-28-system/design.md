## Context

The `py-agent-core` project is a greenfield Python library that provides a lightweight, non-opinionated, and event-driven runtime loop for AI agents. It prioritizes low-level execution control, automatic schema parsing for python tools, and instant, transport-level cooperative interruption.

## Goals / Non-Goals

**Goals:**
- Provide a `PyAgent` class that runs an asynchronous agent execution loop (User input -> LLM completion stream -> Tool invocation -> Continuation).
- Emits granular, type-safe execution events (`AgentEvent`).
- Implement transport-level stream interruption by closing the HTTP connection as soon as an interrupt flag is checked.
- Provide a `@tool` decorator that compiles standard Python functions into LLM-compatible tool definitions through signature and docstring analysis.
- Support hierarchical agent execution implicitly by allowing agents to run nested within other agents' tools.
- Decouple the core execution loop from vendor-specific SDKs by using a unified `BaseBackend` abstraction.

**Non-Goals:**
- Tree-structured conversation histories (deferred to the backlog).
- Complex orchestration features like built-in multi-agent routers or state charts.
- Built-in persistent databases or UI interfaces.

## Decisions

### 1. Tool Metadata Extraction via Introspection
- **Option A (Chosen):** Automatically parse type hints and docstrings using the standard `inspect` module and standard type schemas. Parameter descriptions will be extracted from google/numpy/sphinx-style docstrings.
- **Option B:** Force the developer to write tool schemas manually in JSON/dict format.
- **Rationale:** Option A provides a superior developer experience, reducing boilerplate while retaining full flexibility.

### 2. Transport-level Interruption Mechanism
- **Option A (Chosen):** Check an `_interrupted` flag before/during LLM streaming and call `await response_stream.close()` (or equivalent transport close method) to terminate the network connection immediately.
- **Option B:** Allow the LLM request to complete and ignore the response post-facto.
- **Rationale:** Option A stops the provider from generating more tokens, saving latency and API costs.

### 3. Hierarchical Execution Design
- **Option A (Chosen):** No explicit hierarchy code in the `PyAgent` class. Child agents are instantiated and run within standard python functions decorated with `@tool`.
- **Option B:** Build a dedicated nested agent registry and sub-agent routing state machine within the framework core.
- **Rationale:** Option A keeps the core loop minimal and transparent. Hierarchies emerge naturally from normal function composition.

### 4. LLM Backend Abstraction
- **Option A (Chosen):** Introduce a clean abstract interface `BaseBackend` with subclasses for `AzureOpenAIBackend`, `OllamaBackend`, and `DummyBackend`. The `PyAgent` receives a backend instance in its constructor and calls `backend.generate_stream(...)`.
- **Option B:** Hardcode OpenAI SDK support inside `PyAgent` and write mock connections/adapters on top.
- **Rationale:** Option A makes the library highly extensible, enabling offline testing via `DummyBackend` and hosting on local infrastructure via `OllamaBackend` with zero changes to `PyAgent`.

## LLM Backend Class Design

The subpackage `py_agent_core.backends` will define:

- `BackendChunk`: A unified representation of a streaming delta containing either text or tool calls.
- `BaseBackend` (ABC):
  ```python
  class BaseBackend(ABC):
      @abstractmethod
      async def generate_stream(
          self, 
          messages: list[dict[str, Any]], 
          tools: Optional[list[dict[str, Any]]] = None
      ) -> AsyncGenerator[BackendChunk, None]:
          pass
  ```
- `AzureOpenAIBackend`: Wraps `AsyncAzureOpenAI` from the `openai` SDK.
- `OllamaBackend`: Wraps the `AsyncClient` from the `ollama` SDK.
- `DummyBackend`: Yields paragraphs of Lorem Ipsum, sleeping briefly between chunks.

## Example Scenarios

We will implement 4 executable examples to showcase and verify these design choices:
1. **`rhetoric_speaker.py`**: A CLI runner running a continuous orator agent. The script concurrently listens for user input; when the user submits a new topic, it invokes `agent.interrupt()`, aborting current output and seamlessly switching topic with elegant transition phrasing.
2. **`hierarchical_assistant.py`**: A nested sub-agent pattern. A parent agent delegates code writing to a writer sub-agent, and code checking to a reviewer sub-agent (both packaged as standard python functions decorated with `@tool`).
3. **`search_watchdog.py`**: Interruption watchdog pattern. A search agent executes multiple slow tools. Concurrently, a watchdog monitors constraints (like safety or timeouts) and triggers `agent.interrupt()` if violated.
4. **`structured_streaming.py`**: Generates and streams structured JSON chunk-by-chunk using OpenAI/Anthropic structured outputs syntax, demonstrating correct event capture for complex JSON.

## Risks / Trade-offs

- **[Risk] Docstring format parsing errors** → *Mitigation:* Fall back gracefully to empty descriptions if docstring format is unrecognized, while logging a warning.
- **[Risk] Connection leakage on close** → *Mitigation:* Wrap client generation in `async with` context managers or ensure robust try/finally resource cleanup when closing streams.
