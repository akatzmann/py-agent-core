## ADDED Requirements

### Requirement: Automatic Schema Generation
The system SHALL provide a decorator `@tool` that automatically introspects a decorated Python function's name, docstring, parameters, and type hints to compile a standard OpenAI/Anthropic tool schema definition.

#### Scenario: Generate schema from standard function
- **WHEN** a Python function with type hints and a structured docstring is decorated with `@tool`
- **THEN** the system SHALL construct a tool definition containing the correct name, parameter properties, types, default values, and parameter descriptions extracted from the docstring.

#### Scenario: Executing a tool function
- **WHEN** the agent loop invokes a decorated tool function with parsed JSON arguments
- **THEN** the system SHALL execute the Python function asynchronously and return its return value formatted as a string.
