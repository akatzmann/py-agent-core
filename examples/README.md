# PyAgentCore Walkthrough: Examples Index & Learning Path

This directory contains executable examples demonstrating the core features of `py-agent-core` — specifically **cooperative preemption**, **zero-opinion event handling**, **tool parser automation**, **sub-agent hierarchy**, and **stream interception**.

> [!TIP]
> **For AI Coding Agents**: All examples support offline execution via the local `DummyBackend` adapter (requiring no API keys or internet access). You can test changes or verify example scripts by running the test suite (`pytest`).

## Context Delegation for AI Coding Agents

Your time is precious. Let your agent build the mental model for these examples.

- **Feed this prompt** to **Antigravity**, **Claude Code**, **OpenClaw**, **OpenCode**, or **GitHub Copilot**.
- Ask it to navigate and understand the examples directory before making any changes.

```text
Read examples/README.md in the py-agent-core repository and explain:
1. What each example demonstrates and which py_agent_core features it exercises.
2. The difference between fundamental and advanced examples.
3. How minimal_coder.py differs from self_healing_coder.py in terms of complexity and goal.
4. The pattern used for user-in-the-loop tool approval.
```

---

## 1. Fundamental Examples

Start here to understand the core programming model and event loop mechanics of `py-agent-core`.

### A. Hello Agent Quickstart (`hello_agent.py`)

A minimal "Hello World" example that instantiates an agent, streams response tokens, and consumes event-driven logs.

```text
               ┌────────────────────────┐
               │  Agent.prompt_stream   │
               └───────────┬────────────┘
                           │ (message_update events)
                           ▼
               ┌────────────────────────┐
               │ Stream to stdout       │
               └────────────────────────┘
```

* **Core Concept**: Bare-minimum async loop setup.
* **Mechanism**: Sets up an `Agent` instance, runs the async runner, and outputs raw token stream responses.

### B. Minimal Coder (`minimal_coder.py`)

The shortest path to a **tool-calling agent** with a human-in-the-loop approval gate:
1. User enters a task (e.g. *"What is the factorial of 12?"*).
2. The LLM writes Python code and calls the `run_python_code` tool.
3. The user is prompted to approve or reject execution.
4. Code runs in a subprocess and the result is returned to the agent.

```text
               ┌───────────────────────┐
               │  agent.prompt_stream  │
               └───────────┬───────────┘
                           │ (tool_call)
                           ▼
               ┌───────────────────────┐
               │  run_python_code tool │
               │  → input("Approve?")  │
               └───────────┬───────────┘
                           │ (subprocess)
                           ▼
               ┌───────────────────────┐
               │  stdout / stderr      │
               └───────────────────────┘
```

* **Core Concept**: `@tool` definition + user-confirmation gate.
* **Mechanism**: Defines one `@tool` function with `asyncio.to_thread(input, ...)` so the approval prompt is non-blocking, then runs a single `Agent.prompt_stream()` loop. Entire example fits in one screen.

### C. Structured Streaming (`structured_streaming.py`)

A simple demonstration of running the event loop, streaming raw tokens, and parsing structured data.

```text
               ┌────────────────────────┐
               │  Agent.prompt_stream   │
               └───────────┬────────────┘
                           │ (message_update events)
                           ▼
               ┌────────────────────────┐
               │ Stream JSON to Terminal│
               └───────────┬────────────┘
                           │ (agent_end event)
                           ▼
               ┌────────────────────────┐
               │ json.loads(complete)   │
               └────────────────────────┘
```

* **Core Concept**: Basic event consumption.
* **Mechanism**: Runs the agent loop, prints the streaming `text_delta` tokens as they arrive, and consolidates the output on an `agent_end` event to parse it as standard JSON.

### D. Search Watchdog (`search_watchdog.py`)

Shows how to abort an agent's execution from an external task if a timeout is reached.

```text
                ┌─────────────────────────────────┐
                │       Watchdog Timer (1s)       │
                └────────────────┬────────────────┘
                                 │ (Sleep & abort)
                                 ▼
         ┌───────────┐        agent.abort()        ┌───────────┐
         │   Agent   │────────────────────────────▶│   Agent   │
         │  Running  │                             │  Aborted  │
         └───────────┘                             └───────────┘
               │
               ▼ (Starts)
        ┌──────────────┐
        │  slow_search │ (Takes 3s)
        └──────────────┘
```

* **Core Concept**: Timeout-based cooperative preemption.
* **Mechanism**: Spawns a background watchdog timer alongside the agent loop. If the agent's registered `slow_search` tool runs longer than the watchdog threshold (1s vs 3s), the watchdog calls `agent.abort()` to abort the runner immediately.

### E. Rhetoric Speaker Monologue (`rhetoric_speaker.py`)

Demonstrates how to interrupt an active speech monologue mid-generation using standard input.

* **Core Concept**: User-initiated live preemption.
* **Mechanism**: Runs an continuous monologue speaking loop. A background input listener reads `sys.stdin`. When the user types a new topic and hits Enter, the listener calls `agent.abort()` to abort the monologue, and the agent uses the new topic to continue speaking.

### F. Hierarchical Assistant (`hierarchical_assistant.py`)

Showcases how to build multi-agent hierarchies by running sub-agents inside standard Python tools.

```text
                ┌─────────────────────────────────┐
                │         Parent Agent            │
                └──────────────┬──────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼ (Calls tool)                ▼ (Calls tool)
       ┌──────────────────┐          ┌──────────────────┐
       │   code_writer    │          │  code_reviewer   │
       │    Sub-Agent     │          │    Sub-Agent     │
       └──────────────────┘          └──────────────────┘
```

* **Core Concept**: Nested execution loops (agents as tools).
* **Mechanism**: Defines `@tool` functions that instantiate and run specialized child sub-agents (a `code_writer` and a `code_reviewer`). The parent coordinator agent calls these tools sequentially to complete a coding request.

---

## 2. Advanced Examples

These examples build on the fundamentals to solve complex, real-world integration challenges.

### A. Interactive TUI Chat (`interactive_chat.py`)

A full interactive terminal chat UI that decouples user keyboard typing from asynchronous streaming output.

```text
┌────────────────────────────────────────────────────────┐
│  Agent Interactive Chat TUI               [STATUS: ○]  │
├────────────────────────────────────────────────────────┤
│ User: Explain quantum superposition.                   │
│ Agent: In quantum mechanics, superposition is a        │
│ fundamental principle where physical systems can       │
│ exist in multiple states simultaneously...             │
├────────────────────────────────────────────────────────┤
│ Type a query (Press any key to interrupt mid-stream):  │
│ > _                                                    │
└────────────────────────────────────────────────────────┘
```

* **Core Concept**: Decoupled interactive terminal preemption.
* **Mechanism**: Uses `prompt_toolkit` to split screen buffers. If the user presses any key while the status is "Streaming", the UI immediately invokes `agent.abort()`, halts the active stream, and captures the keystroke as the start of the next query.

### B. Streaming Guardrails & Masking Interceptor (`guardrail_streaming.py`)

A token-by-token stream interceptor that filters PII data and interrupts generation on blocked content.

```text
               ┌───────────────────────┐
               │  LLM Backend Generator│
               └───────────┬───────────┘
                           │ (Stream of BackendChunks)
                           ▼
               ┌───────────────────────┐
               │   Guardrail Interceptor│
               └───────────┬───────────┘
                           │ (Inspects & checks matches)
             ┌─────────────┴─────────────┐
             ▼ (Censored / Redacted)     ▼ (Toxic / Blocked)
       Censor stream content       1. Calls agent.abort()
       (e.g. user@email.com        2. Yields 'interrupted' event
        -> [REDACTED])             3. Stops yielding deltas
```

* **Core Concept**: Non-intrusive stream middleware.
* **Mechanism**: An async generator wrapper processes the agent stream. It uses word-buffering to prevent token-split regex evasion, replaces emails with redact placeholders, and immediately calls `agent.abort()` if blocked content keywords appear.

### C. Parallel Agent Swarm (`agent_swarm.py`)

Shows how to run multiple independent agents concurrently using native async Python loops.

```text
                       ┌──────────────────────┐
                       │  User Request Prompt │
                       └──────────┬───────────┘
                                  ▼
                     ┌────────────────────────────┐
                     │  asyncio.gather() Spawns:  │
                     └──────┬──────────────┬──────┘
                            │              │
         ┌──────────────────┴──┐        ┌──┴──────────────────┐
         │  Researcher Agent   │        │   Outline Agent     │
         │  (Calls slow tools) │        │  (Drafts structure) │
         └──────────────────┬──┘        └──┬──────────────────┘
                            │                  │
                            └──────────┬───────┘
                                      ▼
                       ┌──────────────────────┐
                       │  Synthesizer Agent   │
                       │ (Builds final piece) │
                       └──────────────────────┘
```

* **Core Concept**: Zero-opinion parallel task execution.
* **Mechanism**: Executes `researcher` and `outliner` concurrently using `asyncio.gather()`. Their event loops are interleaved and printed to the terminal with custom prefixes, and the outputs are synthesized by a final coordinator agent.

### D. Self-Healing Developer Loop (`self_healing_coder.py`)

An autonomous code writer that executes scripts in subprocesses and auto-corrects runtime/syntax errors.

```text
                 ┌─────────────────────────────────┐
                 │        Agent: Write Code        │
                 └────────────────┬────────────────┘
                                  │
                                  ▼
                 ┌─────────────────────────────────┐
                 │  Tool: execute_python_code()   │
                 └────────────────┬────────────────┘
                                  │
                                  ▼
                      Code compiles & runs?
                      ┌───────────┴───────────┐
                      ▼ (No: Exception)       ▼ (Yes: Success)
              Feed traceback to Agent      Complete task
              (Agent corrects syntax/logic)
```

* **Core Concept**: Code interpreter tool integration & context healing.
* **Mechanism**: The agent is exposed to a Python subprocess runner tool. If execution fails, the traceback is returned to the agent's context, letting it inspect the syntax or runtime error and execute corrected code iteratively.

### E. Advanced Agent Features (`advanced_agent_features.py`)

A comprehensive showcase of stateful Agent configurations, telemetry subscriptions, interception hooks, parallel executions, custom pipelines, and queue steering.

```text
 ┌────────────────────────────────────────────────────────┐
 │           ADVANCED AGENT FEATURES DEMO FLOW            │
 └────────────────────────────────────────────────────────┘
                              │
                    1. Subscribe Callback
                              ▼
        ┌──────────────────────────────────────────┐
        │  Event Listener Callback (Audit Logger)  │
        └──────────────────────────────────────────┘
                              │
                    2. Prompt Execution
                              ▼
            ┌───────────────────────────────┐
            │   LLM decides to call Tool    │
            └───────────────┬───────────────┘
                            │
               3. Intercept via before_tool_call Hook
                            ▼
            ┌───────────────────────────────┐
            │      Human Approval Gate      │
            │ "Allow execute_command? [y/N]"│
            └───────────────┬───────────────┘
                            │
                      ┌─────┴─────┐
                   Yes│         No│
                      ▼           ▼
               ┌──────────┐   ┌──────────┐
               │ Execute  │   │  Reject  │
               │  Tool    │   │  & Abort │
               └──────────┘   └──────────┘
                              │
              4. Active Steering / Follow-up Queues
                              ▼
            ┌───────────────────────────────┐
            │   steer(): inject prompt      │
            │   follow_up(): queue plan     │
            └───────────────────────────────┘
```

* **Core Concept**: Comprehensive stateful Agent lifecycle orchestration.
* **Mechanism**: Sets up decoupled console audit loggers via `.subscribe()`, hooks a terminal verification gate into `before_tool_call`, filters and terminates output in `after_tool_call`, parallelizes fetch queries in `tool_execution="parallel"`, rewrites and prunes message history in `convert_to_llm` / `transform_context`, and injects prompts dynamically mid-run and post-run via `steer()` and `follow_up()`.

---

## Running the Examples

All examples support the standard command-line backend flags (`--backend`, `--model`, `--endpoint`, `--api-key`).

### Running Offline (Default)
By default, examples run with a local `DummyBackend` requiring no API keys or internet connection:
```bash
python -m examples.hello_agent
python -m examples.minimal_coder
python -m examples.structured_streaming
python -m examples.search_watchdog
python -m examples.rhetoric_speaker
python -m examples.hierarchical_assistant
python -m examples.interactive_chat
python -m examples.guardrail_streaming
python -m examples.agent_swarm
python -m examples.self_healing_coder
python -m examples.advanced_agent_features
```

### Running with a Local Model (Ollama)
```bash
python -m examples.hello_agent --backend ollama --model qwen3-4b-instruct-2507:latest --endpoint http://localhost:11434
```
