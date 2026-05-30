# PyAgentCore Walkthrough: Examples Index & Learning Path

This directory contains executable examples demonstrating the core features of `py-agent-core` — specifically **cooperative preemption**, **zero-opinion event handling**, **tool parser automation**, **sub-agent hierarchy**, and **stream interception**.

> [!TIP]
> **For AI Coding Agents**: All examples support offline execution via the local `DummyBackend` adapter (requiring no API keys or internet access). You can test changes or verify example scripts by running the test suite (`pytest`).

---

## 1. Fundamental Examples

Start here to understand the core programming model and event loop mechanics of `py-agent-core`.

### A. Hello Agent Quickstart (`hello_agent.py`)

A minimal "Hello World" example that instantiates an agent, streams response tokens, and consumes event-driven logs.

```text
               ┌───────────────────────┐
               │    PyAgent.run_loop   │
               └───────────┬───────────┘
                           │ (text_delta events)
                           ▼
               ┌───────────────────────┐
               │ Stream to stdout      │
               └───────────────────────┘
```

* **Core Concept**: Bare-minimum async loop setup.
* **Mechanism**: Sets up a `PyAgent` instance, runs the async runner, and outputs raw token stream responses.

### B. Structured Streaming (`structured_streaming.py`)

A simple demonstration of running the event loop, streaming raw tokens, and parsing structured data.

```text
               ┌───────────────────────┐
               │    PyAgent.run_loop   │
               └───────────┬───────────┘
                           │ (text_delta events)
                           ▼
               ┌───────────────────────┐
               │ Stream JSON to Terminal│
               └───────────┬───────────┘
                           │ (done event)
                           ▼
               ┌───────────────────────┐
               │ json.loads(complete)  │
               └───────────────────────┘
```

* **Core Concept**: Basic event consumption.
* **Mechanism**: Runs the agent loop, prints the streaming `text_delta` tokens as they arrive, and consolidates the output on a `done` event to parse it as standard JSON.

### C. Search Watchdog (`search_watchdog.py`)

Shows how to abort an agent's execution from an external task if a timeout is reached.

```text
                ┌─────────────────────────────────┐
                │       Watchdog Timer (1s)       │
                └────────────────┬────────────────┘
                                 │ (Sleep & interrupt)
                                 ▼
         ┌───────────┐      agent.interrupt()      ┌───────────┐
         │  PyAgent  │────────────────────────────▶│   Agent   │
         │  Running  │                             │  Aborted  │
         └───────────┘                             └───────────┘
               │
               ▼ (Starts)
        ┌──────────────┐
        │  slow_search │ (Takes 3s)
        └──────────────┘
```

* **Core Concept**: Timeout-based cooperative preemption.
* **Mechanism**: Spawns a background watchdog timer alongside the agent loop. If the agent's registered `slow_search` tool runs longer than the watchdog threshold (1s vs 3s), the watchdog calls `agent.interrupt()` to abort the runner immediately.

### D. Rhetoric Speaker Monologue (`rhetoric_speaker.py`)

Demonstrates how to interrupt an active speech monologue mid-generation using standard input.

* **Core Concept**: User-initiated live preemption.
* **Mechanism**: Runs an infinite monologue speaking loop. A background input listener reads `sys.stdin`. When the user types a new topic and hits Enter, the listener calls `agent.interrupt()` to abort the monologue, and the agent uses the new topic to continue speaking.

### E. Hierarchical Assistant (`hierarchical_assistant.py`)

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
│  PyAgent Interactive Chat TUI             [STATUS: ○]  │
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
* **Mechanism**: Uses `prompt_toolkit` to split screen buffers. If the user presses any key while the status is "Streaming", the UI immediately invokes `agent.interrupt()`, halts the active stream, and captures the keystroke as the start of the next query.

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
       Censor stream content       1. Calls agent.interrupt()
       (e.g. user@email.com        2. Yields 'interrupted' event
        -> [REDACTED])             3. Stops yielding deltas
```

* **Core Concept**: Non-intrusive stream middleware.
* **Mechanism**: An async generator wrapper processes the agent stream. It uses word-buffering to prevent token-split regex evasion, replaces emails with redact placeholders, and immediately calls `agent.interrupt()` if blocked content keywords appear.

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
* **Mechanism**: Executes `ResearcherAgent` and `OutlineAgent` concurrently using `asyncio.gather()`. Their event loops are interleaved and printed to the terminal with custom prefixes, and the outputs are synthesized by a final coordinator agent.

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

---

## Running the Examples

All examples support the standard command-line backend flags (`--backend`, `--model`, `--endpoint`, `--api-key`).

### Running Offline (Default)
By default, examples run with a local `DummyBackend` requiring no API keys or internet connection:
```bash
python -m examples.hello_agent
python -m examples.structured_streaming
python -m examples.search_watchdog
python -m examples.rhetoric_speaker
python -m examples.hierarchical_assistant
python -m examples.interactive_chat
python -m examples.guardrail_streaming
python -m examples.agent_swarm
python -m examples.self_healing_coder
```

### Running with a Local Model (Ollama)
```bash
python -m examples.interactive_chat --backend ollama --model llama3
```
