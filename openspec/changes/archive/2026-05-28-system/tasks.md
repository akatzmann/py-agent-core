## 1. Project Setup

- [x] 1.1 Create the package directory structure (`py_agent_core/` modules) and project files (`pyproject.toml`, `setup.py`, `README.md`).
- [x] 1.2 Implement core exports in `py_agent_core/__init__.py`.

## 2. Tool Parser Implementation

- [x] 2.1 Create the `@tool` decorator in `py_agent_core/tool.py`.
- [x] 2.2 Implement signature, type hint, and docstring introspection to auto-generate OpenAI/Anthropic-style JSON tool schemas.
- [x] 2.3 Implement the argument parser and async executor inside the decorated tool wrapper.

## 3. LLM Backend Abstraction

- [x] 3.1 Create the `BaseBackend` interface and `BackendChunk` classes in `py_agent_core/backends/base.py`.
- [x] 3.2 Implement the `AzureOpenAIBackend` adapter using the `openai` SDK.
- [x] 3.3 Implement the `OllamaBackend` adapter using the `ollama` SDK.
- [x] 3.4 Implement the `DummyBackend` mock adapter generating simulated Lorem Ipsum stream deltas.

## 4. Core Agent Loop

- [x] 4.1 Define the `AgentEvent` and event type definitions in `py_agent_core/agent.py`.
- [x] 4.2 Implement the `PyAgent` class constructor accepting a `BaseBackend` instance.
- [x] 4.3 Implement `run_loop` async generator to request completions from the backend, parsing and yielding `text_delta` and `done` events.
- [x] 4.4 Integrate tool calling execution into the core execution loop and yield `tool_start` and `tool_end` events.

## 5. Interruption & Preemption

- [x] 5.1 Implement the `interrupt()` method to toggle the internal interrupt flag.
- [x] 5.2 Implement cooperative preemption checks inside the token streaming loop, closing the active backend's response stream on interrupt.
- [x] 5.3 Implement interrupt verification before executing tools.

## 6. Verification & Demos

- [x] 6.1 Create automated tests for the `@tool` schema parser.
- [x] 6.2 Create automated tests for the unified LLM backends (particularly `DummyBackend`).
- [x] 6.3 Create automated tests for the core execution loop and the interruption mechanics.
- [x] 6.4 Implement the rhetoric monologue demo (`examples/rhetoric_speaker.py`) with continuous CLI speech and user-triggered interrupts.
- [x] 6.5 Implement the hierarchical assistant demo (`examples/hierarchical_assistant.py`) demonstrating nested sub-agent tool calls.
- [x] 6.6 Implement the watchdog monitoring demo (`examples/search_watchdog.py`) demonstrating mid-execution preemption.
- [x] 6.7 Implement the structured data generation demo (`examples/structured_streaming.py`) showing structured stream event yields.
- [x] 6.8 Add automated integration tests verifying each example runs successfully using mock inputs and simulated backends.
