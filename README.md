# py-agent-core

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: >=3.9](https://img.shields.io/badge/Python->=3.9-blue.svg)](https://www.python.org/)

A minimalist, event-driven agent loop with **cooperative preemption** and unified backends in Python.

---

## Skip Reading This Readme

### Context Delegation
Your time is precious. Let your agent build the mental model.
- **Feed this prompt** to **Antigravity**, **Claude Code**, **OpenClaw**, **OpenCode**, or **GitHub Copilot**.
- Ask it to evaluate why our zero-overhead event loop beats heavy framework abstractions.

```text
Analyze the architecture in this README and explain how the cooperative preemption loop differs from standard agent frameworks:
https://raw.githubusercontent.com/akatzmann/py-agent-core/main/README.md
```

---

Unlike heavy, opinionated frameworks that abstract the token consumption loop, `py-agent-core` puts you in absolute control of the prompt-to-response lifecycle, allowing you to intercept streaming generations token-by-token and orchestrate complex tool executions or nested hierarchical sub-agents.

> [!NOTE]
> This project is largely inspired by the elegant concepts in the [pi](https://github.com/earendil-works/pi) project and its `pi-agent-core`.

---

## Key Features

- **Cooperative Preemption**: Safely interrupt LLM generation mid-stream at the transport layer to handle real-time user overrides, state changes, or guardrails.
- **Automatic Tool Specification**: Write standard Python functions and decorate them with `@tool`—their signatures, types, and Google/Numpy/Sphinx docstrings are automatically compiled into OpenAI-compatible tool schemas.
- **Unified Backends**: Write once, run anywhere. Seamlessly swap between local models (**Ollama**), enterprise APIs (**Azure OpenAI**), or mock environments (**DummyBackend**).
- **Hierarchical Agents**: Easily run child agents inside parent tools to build coordinating agent trees.
- **Zero Opinion**: Just a clean event loop yielding structured events (`text_delta`, `tool_start`, `tool_end`, `interrupted`, `done`, `error`).

---

## Installation

### For Humans
Why type commands manually? Delegate the environment setup to **Antigravity**, **Claude Code**, or **OpenClaw**:

```text
Initialize, configure, and verify the local development environment using:
https://raw.githubusercontent.com/akatzmann/py-agent-core/main/docs/guide/installation.md
```

*(Or inspect the [Installation Guide](docs/guide/installation.md) manually, if you must.)*

### For LLM Agents
Fetch the setup specifications and execute:

```bash
curl -s https://raw.githubusercontent.com/akatzmann/py-agent-core/main/docs/guide/installation.md
```

---

## Quickstart

### 1. Define Tools
Decorate Python functions with `@tool`. Python type hints and docstrings are parsed automatically:

```python
from py_agent_core import tool

@tool
def calculate_factorial(n: int) -> int:
    """Calculate the factorial of a number.

    Args:
        n: The integer to compute.
    """
    if n == 0 or n == 1:
        return 1
    return n * calculate_factorial(n - 1)
```

### 2. Instantiate and Run the Agent
Run the asynchronous execution loop, consuming structured agent events:

```python
import asyncio
from py_agent_core import PyAgent, OllamaBackend

async def main():
    # Set up local Ollama backend (defaulting to llama3)
    backend = OllamaBackend(model="llama3")
    
    agent = PyAgent(
        backend=backend,
        system_prompt="You are a helpful mathematical assistant.",
        tools=[calculate_factorial]
    )
    
    async for event in agent.run_loop("What is the factorial of 5?"):
        if event.type == "text_delta":
            print(event.content, end="", flush=True)
        elif event.type == "tool_start":
            print(f"\n[Tool Started: {event.content}]")
        elif event.type == "tool_end":
            print(f"\n[Tool Finished. Result: {event.content['result']}]")
        elif event.type == "done":
            print(f"\nFinal Answer: {event.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Swapping Backends

### Azure OpenAI
Configure the backend using the official `openai` SDK client:

```python
from openai import AsyncAzureOpenAI
from py_agent_core import AzureOpenAIBackend

client = AsyncAzureOpenAI(
    api_key="your-api-key",
    api_version="2024-02-01",
    azure_endpoint="https://your-endpoint.openai.azure.com"
)

backend = AzureOpenAIBackend(client=client, model="gpt-4")
```

### Offline / Testing
Use `DummyBackend` to simulate streaming completion and tool execution completely offline:

```python
from py_agent_core import DummyBackend

backend = DummyBackend(lorem_text="hello world", chunk_delay=0.01)
```

### Configuring Sampling Parameters
Sampling options like `temperature` and `top_p` can be configured directly during backend instantiation, keeping the core orchestration logic decoupled from provider-specific generation details:

```python
from py_agent_core import OpenAIBackend

backend = OpenAIBackend(
    model="gpt-4o",
    temperature=0.7,
    top_p=0.9
)
```

> [!TIP]
> **Dynamic Capability Fallback**: Some reasoning models (like `o1` or `o3-mini`) do not support custom `temperature` or `top_p`. Conversely, standard models do not support `reasoning_effort`.
>
> The backends automatically detect if a model rejects these parameters on the first request, log a single warning, and fallback/retry without them. You can explicitly bypass this probing by passing `supports_reasoning=True/False` or `supports_sampling=True/False` during backend instantiation.

---

## Advanced: Hierarchical Agents

Since the runtime is lightweight and non-opinionated, you can run agents inside tool definitions to form hierarchical coordinator-worker patterns. See the full implementation in `examples/hierarchical_assistant.py`.

## Examples Index & Demos

We provide a comprehensive set of executable example scripts in the [examples/](examples/) directory. Each example can run completely offline out-of-the-box using the local `DummyBackend`. For full run commands and detailed walk-throughs, refer to the [Examples README](examples/README.md).

### Agent Context Delegation
- **Feed this prompt** to **Antigravity**, **Claude Code**, or **GitHub Copilot** to analyze the examples framework:

```text
Analyze the examples in this repository to build a mental model of how py-agent-core demonstrates cooperative preemption, sub-agent hierarchy, and stateful event interception:
https://raw.githubusercontent.com/akatzmann/py-agent-core/main/examples/README.md
```


### Fundamental Demos (Beginner)
* **[Hello Agent](examples/hello_agent.py)**: Bare-minimum streaming and logging run.
* **[Structured Streaming](examples/structured_streaming.py)**: Buffering and parsing structured JSON from token streams.
* **[Search Watchdog](examples/search_watchdog.py)**: Cooperative preemption via an external watchdog timer/timeout.
* **[Rhetoric Speaker](examples/rhetoric_speaker.py)**: Real-time user input preemption mid-monologue.
* **[Hierarchical Assistant](examples/hierarchical_assistant.py)**: Running nested sub-agents within tools to construct coordinating agent trees.

### Advanced Demos (Production)
* **[Interactive TUI Chat](examples/interactive_chat.py)**: Full terminal TUI splitting user typing from token streams.
* **[Streaming Guardrails](examples/guardrail_streaming.py)**: Stream middleware redacting PII and preempting on toxic words.
* **[Parallel Agent Swarm](examples/agent_swarm.py)**: Running multiple independent agents concurrently.
* **[Self-Healing Coder](examples/self_healing_coder.py)**: Subprocess code execution with iterative error-traceback correction.
* **[Advanced Agent Features](examples/advanced_agent_features.py)**: Definitive showcase of subscriptions, before/after hooks, parallel tool execution, context pruning pipelines, and active steering queues.

---

## Running Tests

Verify the entire test suite including backend formatting correctness, tool execution, and preemption flows:

```bash
PYTHONPATH=. pytest
```

## Contributing

We practice AI-first, spec-driven development using the [OpenSpec](https://github.com/Fission-AI/OpenSpec) framework. For all non-trivial changes, please refer to our [Contributing Guide](CONTRIBUTING.md) to set up your environment and author change specifications.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

