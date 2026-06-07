## 1. Core Event Model and Low-level Loop

- [x] 1.1 Define event dataclasses for the turn lifecycle: `agent_start`, `turn_start`, `message_start`, `message_update`, `message_end`, `tool_execution_start`, `tool_execution_update`, `tool_execution_end`, `turn_end`, `agent_end`, `interrupted`, `error`.
- [x] 1.2 Implement the low-level stateless async generator functions `agent_loop` and `agent_loop_continue` using `AgentContext` and `AgentLoopConfig`.
- [x] 1.3 Update existing LLM backends (AzureOpenAI, Ollama, Dummy) to output granular streaming chunks.

## 2. Stateful Agent Orchestrator

- [x] 2.1 Implement the high-level `Agent` class managing `AgentState` (systemPrompt, model, tools, messages).
- [x] 2.2 Add `Agent.subscribe` listener registration and notifications.
- [x] 2.3 Implement the `Agent.prompt` and `Agent.continue` methods yielding events to support the generator consumer model.
- [x] 2.4 Implement state controls: `abort()`, `reset()`, and `waitForIdle()`.

## 3. Tool Execution and Hooks

- [x] 3.1 Implement parallel tool execution using `asyncio.gather` and support per-tool or global sequential fallbacks.
- [x] 3.2 Implement `before_tool_call` interceptor hook (allowing execution blocking).
- [x] 3.3 Implement `after_tool_call` interceptor hook (allowing output rewriting and termination flags).
- [x] 3.4 Support the tool `terminate` hint to gracefully stop the LLM follow-up.

## 4. Context Pipelines and Message Queuing

- [x] 4.1 Integrate `convert_to_llm` and `transform_context` hooks inside the loop execution context.
- [x] 4.2 Implement active steering queue (`agent.steer()`) and follow-up queue (`agent.follow_up()`) processing.
- [x] 4.3 Add queue clear helper methods (`clear_steering_queue`, `clear_follow_up_queue`, `clear_all_queues`).
- [x] 4.4 Integrate `prepare_next_turn` and `should_stop_after_turn` controls in the loop turn boundaries.

## 5. Verification and Deprecation

- [x] 5.1 Implement a backward-compatibility layer mapping legacy `PyAgent` calls to the new `Agent` architecture.
- [x] 5.2 Update existing test suite (`tests/test_agent.py`) to use the new event-driven architecture.
- [x] 5.3 Write new tests covering concurrent tool execution, hooks, steering/follow-up queues, and custom messages.
