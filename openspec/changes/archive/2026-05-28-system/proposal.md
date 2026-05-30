## Why

Modern Python agent frameworks (e.g. AutoGen, LangChain) are overly opinionated, complex, and lack low-latency, transport-level preemption for streaming token generation. Python developers need a minimalist, loop-centric, and non-opinionated library (`py-agent-core`) that provides raw execution control, easy tool definitions, and native, cooperative mid-stream interruption.

## What Changes

- Initialize a greenfield Python package called `py_agent_core`.
- Create a `PyAgent` execution runner class that manages the async agent run loop (User Prompt -> LLM Stream -> Tool Execution -> Loop).
- Support cooperative, transport-level preemption by checking an interrupt flag during token streaming and immediately terminating/closing the HTTP connection if set.
- Implement a unified async LLM backend abstraction interface (`py_agent_core.models` or `py_agent_core.backends`) to decouple the agent loop from specific provider SDKs.
- Implement concrete backend adapters for:
  - `AzureOpenAI`: Integrates with Azure Hosted OpenAI models.
  - `Ollama`: Integrates with local Ollama service instances.
  - `DummyBackend`: A mock adapter that simulates streaming text generation via Lorem Ipsum generator.
- Implement a decorator `@tool` that parses Python function signatures, type hints, and docstrings to automatically generate JSON-schema specifications for tool definitions.
- Implement an `AgentEvent` system to stream granular execution events (`text_delta`, `tool_start`, `tool_end`, `interrupted`, `done`) back to the caller.
- Support hierarchical agent execution by letting developers invoke nested `PyAgent` instances as standard python tools decorated with `@tool`.
- Create 4 executable example scenarios in the `examples/` directory:
  1. `rhetoric_speaker.py`: Interactive CLI with a continuously talking rhetoric agent. The user can enter a new topic at any time, interrupting the agent and forcing it to elegantly transition to the new topic.
  2. `hierarchical_assistant.py`: A coordinator agent invoking `writer` and `reviewer` sub-agents as tools.
  3. `search_watchdog.py`: A watchdog system interrupting long-running search operations or streaming completion if a simulated safety hazard or external timeout triggers.
  4. `structured_streaming.py`: An agent generating structured JSON output token-by-token, demonstrating structured parsing and event extraction.

## Capabilities

### New Capabilities
- `core-runner`: A minimalist, interruptible, event-driven async agent loop class.
- `tool-parser`: A decorator that automatically introspects Python functions to construct LLM-compatible tool definitions.
- `llm-backends`: Unified async backend abstraction with concrete implementations for AzureOpenAI, Ollama, and DummyBackend.

### Modified Capabilities
<!-- None -->

## Impact

- Greenfield project: Creates a new Python library structure, including `setup.py`/`pyproject.toml` and standard package modules under `py_agent_core/`.
- No impact on existing codebases.
