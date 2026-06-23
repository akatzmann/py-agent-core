# py-agent-core

[![PyPI version](https://badge.fury.io/py/py-agent-core.svg)](https://badge.fury.io/py/py-agent-core)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Support](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://pypi.org/project/py-agent-core/)

A minimalist, event-driven agent loop with **cooperative preemption** and unified backends in Python.

> [!NOTE]
> 🏛️ **Architecture Heritage**  
> This project is a Python implementation closely aligned with the elegant engineering concepts behind [pi-agent-core](https://github.com/earendil-works/pi), the TypeScript engine powering systems like OpenClaw.

---

> [!IMPORTANT]
> 🤖 **Using an AI Coding Assistant (Claude Code, Antigravity, Copilot)?**  
> Skip reading this README. Copy-paste the prompt below to let your assistant build the mental model for you:
> ```text
> Explain how py-agent-core's preemption loop differs from standard agent frameworks:
> https://raw.githubusercontent.com/akatzmann/py-agent-core/main/README.md
> ```

---

## ⚡ The Core Value: Why Cooperative Preemption?

Traditional frameworks treat ChatCompletion calls as monolithic black boxes. If a user tries to cancel or override the agent mid-sentence, the runtime is blocked until the generation finishes or the task is crudely killed.

`py-agent-core` handles preemption at the transport layer. By checking an interrupt flag during token consumption, it severs the network socket instantly when triggered—saving latency, tokens, and allowing immediate cognitive redirection.

```text
               THE COOPERATIVE PREEMPTION LOOP
               
  [User App]                     [PyAgent]                    [LLM API]
      │                              │                             │
      │ ─── agent.run_loop() ──────► │                             │
      │                              │ ─── Stream Request ───────► │
      │                              │                             │
      │ ◄── event: text_delta ────── │ ◄── Token Stream ────────── │
      │ ◄── event: text_delta ────── │ ◄── Token Stream ────────── │
      │                              │                             │
      │ ─── agent.interrupt() ─────► │                             │
      │                              │ ─── stream.close() ────────►X (Socket Closed)
      │ ◄── event: interrupted ───── │                             │
```

---

## 🔍 How It Compares

| Architectural Dimension | `py-agent-core` | Big-Box Frameworks |
| :--- | :--- | :--- |
| **🔄 Control Paradigm** | **⚡ Stream of Events (Async Generator)**<br>Yields raw events (`text_delta`, `tool_start`, etc.) | **📥 Callback Managers**<br>Hides execution behind custom routers |
| **🛑 Stream Preemption** | **✅ Surgical Transport-Level Abort**<br>Closes socket connection mid-generation instantly | **❌ Thread Kill / No Cancel**<br>Must wait for the LLM to finish speaking |
| **🧩 Tool Specifications** | **✅ Auto-parsed Typehints & Docstrings**<br>Decorate standard Python functions with `@tool` | **⚠️ Manual Declarations**<br>Requires complex Pydantic schemas or JSON |
| **🎯 Model Resilience** | **✅ Dynamic Parameter Fallback**<br>Gracefully falls back when reasoning vs sampling parameters clash | **❌ SDK Schema Crash**<br>Crashes if a parameter is not supported by the model |
| **🌳 Agent Hierarchy** | **✅ Nested Worker Trees**<br>Instantiate child agents directly inside parent tools | **❌ Complex Graph Configs**<br>Requires custom routers and state channels |
| **📦 Footprint & Bloat** | **✅ Zero-Dependency Core**<br>Minimalist loop code you can read and fit in your head | **❌ Sprawling Class Hierarchy**<br>Hundreds of helper wrappers and utilities |

---

## Quickstart (Run 100% Locally)

### 1. Install
```bash
pip install py-agent-core
```
*(For full local development environment setup instructions, refer to the [Installation Guide](docs/guide/installation.md).)*

### 2. Define a Tool
Write standard Python functions. Their signatures, type hints, and docstrings compile into tool schemas automatically.
```python
from py_agent_core import tool

@tool
def calculate_factorial(n: int) -> int:
    """Compute the factorial of n.
    Args:
        n: The target integer.
    """
    return 1 if n <= 1 else n * calculate_factorial(n - 1)
```

### 3. Run the Event Loop (Ollama)
Consume the stream as structured events in real time:
```python
import asyncio
from py_agent_core import PyAgent, OllamaBackend

async def main():
    # Runs completely offline using a local model (llama3)
    backend = OllamaBackend(model="llama3")
    agent = PyAgent(backend=backend, tools=[calculate_factorial])
    
    async for event in agent.run_loop("Calculate the factorial of 5"):
        if event.type == "text_delta":
            print(event.content, end="", flush=True)
        elif event.type == "tool_start":
            print(f"\n[Tool Started: {event.content}]")
        elif event.type == "tool_end":
            print(f"\n[Tool Finished: {event.content['result']}]")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🛠️ Swapping LLM Backends

Switching between provider endpoints requires zero changes to your agent logic:

### OpenAI / Azure OpenAI
Configure your target endpoints using the official SDK client objects:
```python
from openai import AsyncOpenAI
from py_agent_core import OpenAIBackend

client = AsyncOpenAI(api_key="sk-...")
backend = OpenAIBackend(client=client, model="gpt-4o")
```

### Offline / Mock Testing
Simulate streaming completion and tool execution completely offline with zero LLM API dependency:
```python
from py_agent_core import DummyBackend

backend = DummyBackend(lorem_text="hello world", chunk_delay=0.01)
```

---

## 💡 Executable Examples & Demos

We provide a comprehensive set of executable scripts in the [examples/](examples/) directory. Each example can run completely offline out-of-the-box using the local `DummyBackend`.

### 🟢 Core Concepts (Beginner)
* **[Hello Agent](examples/hello_agent.py)**: Bare-minimum streaming and logging run.
* **[Structured Streaming](examples/structured_streaming.py)**: Buffering and parsing structured JSON from token streams.
* **[Search Watchdog](examples/search_watchdog.py)**: Cooperative preemption via an external watchdog timer/timeout.
* **[Rhetoric Speaker](examples/rhetoric_speaker.py)**: Real-time user input preemption mid-monologue.
* **[Hierarchical Assistant](examples/hierarchical_assistant.py)**: Running nested sub-agents within tools to construct coordinating agent trees.

### 🟡 Production Patterns (Advanced)
* **[Streaming Guardrails](examples/guardrail_streaming.py)**: Stream middleware redacting PII and preempting on toxic words.
* **[Interactive TUI Chat](examples/interactive_chat.py)**: Full terminal TUI splitting user typing from token streams.
* **[Self-Healing Coder](examples/self_healing_coder.py)**: Subprocess code execution with iterative error-traceback correction.
* **[Parallel Agent Swarm](examples/agent_swarm.py)**: Running multiple independent agents concurrently.
* **[Advanced Agent Features](examples/advanced_agent_features.py)**: Complete showcase of subscriptions, before/after hooks, parallel tool execution, context pruning pipelines, and active steering queues.

---

## Running Tests

Verify the entire test suite including backend formatting correctness, tool execution, and preemption flows:

```bash
PYTHONPATH=. pytest
```

## Contributing

We practice AI-first, spec-driven development using the [OpenSpec](https://github.com/Fission-AI/OpenSpec) framework. For all non-trivial changes, please refer to our [Contributing Guide](CONTRIBUTING.md) to set up your environment and author change specifications.

## License

`py-agent-core` is open-source software licensed under the [MIT License](LICENSE).
