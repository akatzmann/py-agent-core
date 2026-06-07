## Context

The library has two extremes in its example portfolio: `hello_agent.py` (pure streaming, no tools) and `self_healing_coder.py` (complex multi-turn feedback loop). A simple, guided coder example in ~30 lines that shows tool definition, tool execution with user approval, and basic `Agent` setup is missing. Existing examples also lack inline comments explaining the "why" behind specific event patterns and constructs.

## Goals / Non-Goals

**Goals:**
- Create `examples/minimal_coder.py` — a script so short it fits on a screen, showcasing: `@tool` definition, user-confirmation gate, and a single `Agent.prompt_stream()` call.
- Add targeted inline comments to existing examples where execution flow, event handling, or hook purpose is non-obvious.

**Non-Goals:**
- Rewriting examples or changing their logic.
- Adding a new UI or interactive TUI to the minimal coder.
- Full test coverage of every comment line added.

## Decisions

### 1. Script Structure of `minimal_coder.py`
- **Choice**: Single `async def main()` function with no helper classes. The `@tool` function, confirmation prompt, and agent loop all live at module level.
- **Rationale**: Minimizing scaffolding is the entire point. Any abstraction or class structure would undermine the "extremely simple" goal.

### 2. User Confirmation via `input()`
- **Choice**: A plain `input("Run this code? [y/N]: ")` inside the `@tool` function body itself, not in a hook.
- **Rationale**: Putting the confirmation directly inside the tool is the most transparent pattern for readers — the approval logic is colocated with the code that runs. It avoids introducing the `before_tool_call` hook concept into a minimal example (that belongs in `advanced_agent_features.py`).

### 3. Suggested Default Prompt
- **Choice**: Print a suggested example task (`"What is the factorial of 12?"`) and let `input()` accept the user's actual task, defaulting to the suggestion.
- **Rationale**: Zero-friction first-run experience — a user can just press Enter and immediately see the full flow.

### 4. Comment Density in Existing Examples
- **Choice**: Add brief single-line comments (`# ...`) only at non-obvious points: event type branching, agent state access patterns, abort/interrupt patterns, and queue usage. Avoid over-commenting trivial lines.
- **Rationale**: Dense comments harm readability. Only add where a reader would otherwise need to consult the docs.

## Risks / Trade-offs

- **[Risk] `input()` blocks async event loop** → *Mitigation*: Use `asyncio.get_event_loop().run_in_executor(None, input, prompt)` inside the async tool so the loop is not blocked. Simpler alternative: since the tool itself is `async`, we can use `await asyncio.to_thread(input, prompt)` (Python 3.9+), which matches our minimum version.
- **[Risk] Script too long to be "minimal"** → *Mitigation*: Keep the target at ≤35 meaningful lines excluding blank lines and the standard `if __name__ == "__main__"` boilerplate. Strip all non-essential imports.
