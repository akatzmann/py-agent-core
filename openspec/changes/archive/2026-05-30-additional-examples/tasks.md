## 1. Setup and Dependencies

- [x] 1.1 Add prompt_toolkit to pyproject.toml under optional-dependencies or core dependencies

## 2. Walkthrough Documentation

- [x] 2.1 Create examples/README.md containing conceptual overview, walkthrough flow, and ASCII diagrams for all four examples

## 3. Example Implementation

- [x] 3.1 Implement examples/interactive_chat.py using prompt_toolkit for uncoupled TUI layout and keypress-triggered agent preemption
- [x] 3.2 Implement examples/guardrail_streaming.py showing PII masking and keyword-based streaming preemption
- [x] 3.3 Implement examples/agent_swarm.py using asyncio.gather to stream research and outline generation in parallel
- [x] 3.4 Implement examples/self_healing_coder.py using subprocess code execution and error traceback recovery

## 4. Verification and Testing

- [x] 4.1 Write tests verifying the behavior of guardrail_streaming wrapper, agent_swarm event multiplexing, and self_healing tool execution
- [x] 4.2 Run the pytest test suite to ensure all tests pass
