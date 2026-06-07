## 1. Create Example Script

- [ ] 1.1 Create `examples/advanced_agent_features.py` boilerplate and initial state config.
- [ ] 1.2 Implement the `console_audit_logger` subscription callback rendering lifecycle events in real-time.
- [ ] 1.3 Implement the `human_approval_gate` before-tool call hook and audit logging in the `after_tool_call` hook.
- [ ] 1.4 Implement parallel mock tools and enable concurrent execution mode.
- [ ] 1.5 Implement custom `convert_to_llm` and `transform_context` hooks to handle custom messages and history pruning.
- [ ] 1.6 Implement the multi-turn dummy agent simulation showcasing dynamic `Agent.steer()` and `Agent.follow_up()` prompts.

## 2. Verification and Documentation

- [ ] 2.1 Add automated test coverage in `tests/test_examples.py` to run `examples/advanced_agent_features.py` in non-interactive mode.
- [ ] 2.2 Update `examples/README.md` to document the new script.
