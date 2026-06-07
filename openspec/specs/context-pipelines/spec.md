# context-pipelines Specification

## Purpose
TBD - created by archiving change architectural-alignment. Update Purpose after archive.
## Requirements
### Requirement: Custom Message Filtering
The system SHALL support filtering and converting custom message structures before sending them to the LLM backend.

#### Scenario: Convert custom messages to LLM format
- **WHEN** the message history contains custom message objects and the `convert_to_llm` hook is configured
- **THEN** the system SHALL invoke the hook to produce a sanitized list of standard LLM messages.

### Requirement: Context Transformation
The system SHALL support transforming the active message history before the translation phase.

#### Scenario: Pruning message history
- **WHEN** the message history grows and a `transform_context` hook is defined
- **THEN** the system SHALL run the hook to prune or modify the messages before they are passed to the backend translator.

