## ADDED Requirements

### Requirement: Active Steering Queue
The system SHALL support queuing steering messages to override or redirect the agent mid-execution.

#### Scenario: Injecting steering messages during tool runs
- **WHEN** steering messages are added via `steer()` while tools are running
- **THEN** the system SHALL finish current active tools, inject the steering messages into history, and trigger a follow-up turn.

### Requirement: Follow-up Queue
The system SHALL support queuing messages to execute after all active tool runs and steering processes have completed.

#### Scenario: Chaining messages
- **WHEN** a message is queued via `follow_up()`
- **THEN** the system SHALL run it as a new turn once the current session becomes idle.
