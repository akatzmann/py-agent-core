## Why

To demonstrate the full potential of `py-agent-core`'s event-driven architecture and cooperative preemption mechanism, we need a set of realistic, complex examples. Developers need to understand how to handle real-world challenges like cursor uncoupling in terminal UIs, content safety filtering/guardrails, parallel agent coordination, and self-healing error correction without framework bloat.

## What Changes

We will introduce four advanced example scripts and a central walkthrough README under the `examples/` directory.

- `examples/interactive_chat.py`: A TUI chat utilizing `prompt_toolkit` to uncouple user input from streaming token outputs and implement live keystroke-based preemption.
- `examples/guardrail_streaming.py`: An interception wrapper showcasing how to inspect, redact, and interrupt token generation streams mid-flight.
- `examples/agent_swarm.py`: A concurrent agent execution pattern leveraging `asyncio.gather` to run researchers and editors in parallel.
- `examples/self_healing_coder.py`: A traceback execution loop where an agent runs code in a subprocess and automatically heals syntax or runtime exceptions based on compiler output.
- `examples/README.md`: A structured learning index detailing the concepts, requirements, and ASCII system flow diagrams for each example.

We will also write unit and integration tests to verify the functionality of these examples.

## Capabilities

### New Capabilities
- `additional-examples`: New advanced example scripts and learning resources demonstrating terminal interfaces, streaming wrappers, swarms, and self-healing agent pipelines.

### Modified Capabilities

## Impact

This change affects only the `examples/` directory and test suites. It introduces no breaking changes to the core `py_agent_core` library and adds optional dev/test dependencies if necessary (like `prompt_toolkit` for the TUI).
