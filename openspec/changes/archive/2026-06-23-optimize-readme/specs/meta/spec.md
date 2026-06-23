## MODIFIED Requirements

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
