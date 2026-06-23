# meta Specification

## Purpose
Specification for repository licensing, ignores, and documentation metadata.
## Requirements
### Requirement: MIT License
The repository SHALL include a root-level LICENSE file containing the standard MIT License.

#### Scenario: Verify LICENSE file
- **WHEN** the project is inspected at the root directory
- **THEN** a LICENSE file SHALL exist and contain the MIT License text.

### Requirement: Ignored env files
The repository SHALL ignore `.env` files in git to prevent credential leaks.

#### Scenario: Verify gitignore configurations
- **WHEN** `.gitignore` is loaded
- **THEN** it SHALL contain a rule to ignore `.env` files.

### Requirement: Comprehensive README documentation
The repository SHALL include a `README.md` at the root optimized for LLM agent ingestion and human reference, containing:
- An architecture heritage note linking to the concepts behind `pi-agent-core`.
- A visual ASCII diagram illustrating the cooperative preemption loop.
- A comparative capabilities matrix using UTF-8 status indicators.
- Local-first quickstart documentation using Ollama.
- Visually distinct context-delegation prompts for AI coding agents positioned immediately below the introductory pitch and architecture heritage note.

#### Scenario: Verify README file
- **WHEN** the project is inspected at the root directory
- **THEN** a README.md file SHALL exist and contain the architecture heritage note, the cooperative preemption diagram, the comparative capabilities matrix with UTF-8 icons, the local-first Ollama quickstart, and the AI agent context-delegation prompts.

### Requirement: Dedicated Installation Guide
The repository SHALL include an installation guide at `docs/guide/installation.md` containing detailed commands to clone, configure virtual environment, and install `py-agent-core`.

#### Scenario: Verify Installation Guide file
- **WHEN** the project is inspected at `docs/guide/installation.md`
- **THEN** the file SHALL exist and contain specific bash commands to set up the package.

