## ADDED Requirements

### Requirement: Command Line Sampling Params Parsing
The system SHALL parse command-line arguments to configure sampling parameters like `temperature` and `top_p` for the backend wrapper.

#### Scenario: Parse custom temperature and top_p
- **WHEN** an example runner script is executed with `--temperature 0.7` and `--top-p 0.9`
- **THEN** the system SHALL instantiate the chosen backend with those configured values.
