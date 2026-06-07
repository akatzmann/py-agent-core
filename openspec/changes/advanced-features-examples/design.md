## Context

The recent architectural alignment added powerful, stateful orchestration features to the `Agent` class (subscriptions, interception hooks, context pipelines, and dynamic queues). To make these features accessible, clear, and easy to implement, we need a dedicated example showcasing best practices for telemetry, human-in-the-loop validation, custom message mapping, and steering.

## Goals / Non-Goals

**Goals:**
- Add a comprehensive example script `examples/advanced_agent_features.py` demonstrating:
  1. Decoupled telemetry/logging via `Agent.subscribe()`.
  2. A human approval gate intercepting tool execution via `before_tool_call`.
  3. Output auditing, modification, or termination via `after_tool_call`.
  4. Parallel tool execution of independent tasks using `asyncio.gather`.
  5. Translating custom UI message structures via `convert_to_llm` and pruning context via `transform_context`.
  6. Dynamic prompt injection mid-run using `Agent.steer()` and `Agent.follow_up()`.
- Run offline by default using the `DummyBackend` or a mock backend.
- Integrate validation tests for the new script in `tests/test_examples.py`.

**Non-Goals:**
- Modifying the core `Agent` or `agent_loop` implementation.
- Building a graphic or web-based UI (the example will remain purely console-driven).

## Decisions

### 1. Interactive vs. Automated Test Execution
- **Choice**: Implement an interactive approval gate in `before_tool_call` using standard `input()` prompts, but bypass or auto-mock it when running inside unit tests (e.g., via command-line arguments `--non-interactive` or patching `sys.stdin`).
- **Rationale**: Keeps the code simple and engaging for manual experimentation while preventing test runs (`pytest`) from hanging in continuous integration.

### 2. Turn-based Mocking in `DummyBackend`
- **Choice**: Use a custom `DummyBackend` subclass in the script that produces multi-turn conversational streams, requests parallel tools, and simulates context pruning.
- **Rationale**: Allows the script to run offline without requiring local LLM setup or API keys, while fully exercising multi-turn logic, hooks, and queue inputs.

### 3. Context Pipeline & Translation Mock
- **Choice**: Define a custom `ui-card` role representing rich UI elements, mapped to standard user messages via `convert_to_llm`, and a basic `transform_context` hook that limits message history to the last 3 messages + system prompt.
- **Rationale**: Demonstrates how real-world applications manage custom UI payloads and prevent tokens limit issues.

## Risks / Trade-offs

- **[Risk] Interactive prompts block test execution** → *Mitigation*: Ensure the command-line interface accepts a `--backend dummy` mode which defaults to non-interactive mock inputs, or check `sys.stdin.isatty()` to auto-approve tool calls during automated test verification.
