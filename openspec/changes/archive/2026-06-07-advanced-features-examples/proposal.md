## Why

The recent architectural alignment introduced advanced stateful capabilities to `Agent` (such as decoupled event subscription, human-in-the-loop tool execution interceptors, context translation/pruning pipelines, and dynamic mid-turn steering/follow-up queues). However, none of the current example scripts showcase these features, leaving them unexposed and untested in realistic user scenarios. Creating a dedicated, feature-rich example will demonstrate best practices for these capabilities in an easy-to-digest manner.

Additionally, the root `README.md` lacks a dedicated index explaining the available examples and their purposes, making it difficult for both humans and AI coding agents to navigate the codebase's examples.

## What Changes

- Add a new comprehensive example script `examples/advanced_agent_features.py`.
- Showcase telemetry/logging using `Agent.subscribe()` to monitor all 11 lifecycle events.
- Showcase human approval / execution gates using the `before_tool_call` hook.
- Showcase output mutation and custom termination flags using the `after_tool_call` hook.
- Showcase parallel tool execution where multiple independent tools execute concurrently via `asyncio.gather`.
- Showcase custom message formatting and context pruning/summarization using the `convert_to_llm` and `transform_context` pipeline hooks.
- Showcase dynamic planning/interaction using `Agent.steer()` and `Agent.follow_up()`.
- Add verification test cases in the test suite to ensure the advanced examples run cleanly.
- Update `examples/README.md` to document the new advanced example.
- Update the root `README.md` to add a dedicated section mapping all examples, helping users and AI agents quickly locate relevant demos.

## Capabilities

### New Capabilities

*(None)*

### Modified Capabilities

- `additional-examples`: Add a new requirement for showcasing advanced agent features (subscriptions, tool hooks, parallel execution, context pipelines, steering queues, and follow-up queues) with a corresponding delta spec.

## Impact

- `examples/advanced_agent_features.py`: New example file.
- `examples/README.md`: Modified to document the new advanced features example.
- `README.md`: Modified to add a dedicated examples section referring to `examples/README.md`.
- `tests/test_examples.py`: Modified to include test validation for the new example.
