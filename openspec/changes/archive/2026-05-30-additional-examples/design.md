## Context

Currently, the examples directory contains a set of basic standalone scripts that showcase simple features. To demonstrate advanced capabilities like async-native cooperative preemption, multiplexed swarms, stream interception wrappers, and traceback self-correction loops, we need new architectures for these examples.

## Goals / Non-Goals

**Goals:**
- Design a CLI TUI for interactive chats that doesn't suffer from mixed output when the user types, using `prompt_toolkit`.
- Design a transparent wrapper to intercept event generators for content guardrails and PII masking.
- Design a parallel agent workflow using `asyncio.gather` that merges events on a single terminal.
- Design a python execution tool and agent loop that handles exceptions and tracebacks to self-heal.
- Provide conceptual documentation and walkthrough indices inside `examples/README.md`.

**Non-Goals:**
- Adding persistent database support (like vectors or RAG) or heavy GUI systems.
- Changing core loop APIs in `py_agent_core`.

## Decisions

### Decision 1: Uncoupling terminal input and output in the interactive chat example
- **Alternative 1:** Standard python `input()` or `sys.stdin.readline`. (Rejected: Prints tokens directly to stdout, disrupting the user's active cursor/typed input).
- **Alternative 2:** Using `Textual` framework. (Rejected: Heavyweight, requires large dependencies, overkill for a lightweight example).
- **Alternative 3:** Using `prompt_toolkit` with `patch_stdout` and an active session. (Chosen: Standard python CLI standard, lightweight, async-native, allows streaming to stdout without corrupting the user prompt input line).

### Decision 2: Guardrail architecture
- **Alternative 1:** Modifying `PyAgent` to take a list of guardrail callbacks. (Rejected: Adds opinionated bloat to the core loop).
- **Alternative 2:** Wrapping the `agent.run_loop` async generator in a helper generator function. (Chosen: Extremely clean, preserves the core's zero-opinion event-driven design. The caller simply filters the events).

### Decision 3: Swarm coordination
- **Alternative 1:** Multi-threaded agent execution. (Rejected: Python GIL, async-first nature of PyAgent makes threads unnecessary).
- **Alternative 2:** Standard asynchronous tasks executing `agent.run_loop()` and merging their events into a common stream. (Chosen: Leverages async event loops cleanly, simple to serialize/prefix text deltas to the console).

### Decision 4: Self-Healing Developer agent tool implementation
- **Alternative 1:** Running code in `exec()` inside the same python process. (Rejected: Highly unsafe, can corrupt the agent workspace or global imports).
- **Alternative 2:** Running code in an isolated subprocess via `sys.executable -c "..."` and capturing `stdout`, `stderr`, and exit code. (Chosen: Safer, provides clean standard traceback output via stderr, mimicking a real developer toolchain).

## Risks / Trade-offs

- **New dependencies:** `prompt_toolkit` is a new dependency. We will add it under optional test/dev dependencies or install it locally for examples.
- **Subprocess execution:** Subprocess execution carries sandbox security risks. We will display clear warnings in the code and restrict it to simple arithmetic scripts.
