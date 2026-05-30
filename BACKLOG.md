# PyAgentCore Backlog

This document outlines features and architectural improvements planned for future iterations of `PyAgentCore` but deferred for the initial implementation.

## 1. Session Tree / Message Graph State

Currently, conversation history is a flat array of messages. This is simple and aligns with standard LLM provider APIs. However, for advanced agent workflows (e.g. debugging, multi-path exploration, branching scenarios), a tree or directed acyclic graph (DAG) structure is desired.

### Features
- **Node-Based History**: Each message or state transition is represented as a node in a tree.
- **Branching / Forking**: Create a new session branch from an arbitrary node ID in the history:
  ```python
  session = AgentSession()
  # ... run loop ...
  # Fork at message 5 to explore an alternative branch
  forked_session = session.fork(node_id="msg_005")
  ```
- **Cloning**: Create an exact deep copy of a session state, retaining all execution history.
- **Backtracking / Reversion**: Easily roll back the conversation state to a previous point in the history.
- **Linearization**: Automatically compile a linear path from the root node to the active leaf node to pass to LLM APIs.
