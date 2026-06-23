## Why

The current README.md is functional but lacks strong visual hooks, competitive positioning, and a friction-free local quickstart, which are critical for driving viral adoption and developer interest on GitHub. Additionally, the meta-agent context delegation prompt, while highly useful, is positioned above the fold, creating unnecessary cognitive load for human developers.

This change aims to optimize the layout of the README to serve both humans and LLM agents optimally, introducing high-impact visual diagrams, a styled UTF-8 comparison table of USPs, and a 100% local-first quickstart using Ollama.

## What Changes

- **Repository Layout & Style**: Polish the root `README.md` to support a visual ASCII preemption flow diagram, a structured comparative capabilities matrix, and clear, styled Markdown badges/callouts.
- **Quickstart**: Update the primary quickstart to use local-first execution via `OllamaBackend`, reducing testing friction.
- **Context Delegation Placement**: Relocate the AI agent context-delegation instructions block to immediately follow the quickstart while keeping it visually distinct as a console card.
- **Architecture Heritage**: Update the project's background attribution to clarify it is closely aligned with `pi-agent-core` (rather than a direct port).

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `meta`: Update the requirements for root-level README documentation to specify inclusion of the cooperative preemption diagram, comparison table with UTF-8 status indicators, and a local-first quickstart.

## Impact

- **Affected Files**: Root `README.md`
- **APIs/Dependencies**: No impact on core application code or APIs.
