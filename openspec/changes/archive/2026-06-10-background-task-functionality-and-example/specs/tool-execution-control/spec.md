## ADDED Requirements

### Requirement: Background Tool Execution
The system SHALL support background non-blocking execution mode for tool calls.

#### Scenario: Running a tool in background mode
- **WHEN** a tool with `execution_mode="background"` is called by the agent
- **THEN** the system SHALL immediately return a status message to the agent loop, schedule the actual execution to run asynchronously on the event loop, and when the execution finishes, inject the result back into the agent context (aborting/steering if active, or queueing as a follow-up if idle) and trigger continuation.
