## MODIFIED Requirements

### Requirement: Comprehensive README documentation
The repository SHALL include a `README.md` at the root optimized for LLM agent ingestion and human reference, delegating detailed setup instructions to separate guides.

#### Scenario: Verify README file
- **WHEN** the project is inspected at the root directory
- **THEN** a README.md file SHALL exist and contain context-delegation prompts, high-level features, quickstart documentation, and references to the installation guide.

## ADDED Requirements

### Requirement: Dedicated Installation Guide
The repository SHALL include an installation guide at `docs/guide/installation.md` containing detailed commands to clone, configure virtual environment, and install `py-agent-core`.

#### Scenario: Verify Installation Guide file
- **WHEN** the project is inspected at `docs/guide/installation.md`
- **THEN** the file SHALL exist and contain specific bash commands to set up the package.
