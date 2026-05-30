## Context

`py-agent-core` README currently details a full setup process which is manual and targets humans. We want to update the repo documentation to align with agent-first ingestion guidelines, providing a context-delegation prompt at the start of the README and delegating installation commands to a separate `docs/guide/installation.md` file.

## Goals / Non-Goals

**Goals:**
- Add a "Skip Reading This Readme" section at the top of the README.
- Add an installation delegation prompt for humans and an installation file fetch instruction for LLM agents in `README.md`.
- Create a clean `docs/guide/installation.md` file containing detailed installation commands.

**Non-Goals:**
- Change python library implementation or backend logic.
- Add complex installation scripts or automation.

## Decisions

### Decision 1: Target raw main branch URLs for LLM agent links
- **Rationale**: Agents require absolute HTTPS paths to read raw markdown files directly using tools or curl.
- **Alternatives Considered**: 
  - Using relative paths: Standard LLM agents cannot easily resolve relative links if they are executing from outside the repo context or loading via URL.
  - Using `master` branch instead of `main`: The repository currently uses the default branch structure, so `main` is selected.

### Decision 2: Splitting installation guide into a separate file under `docs/guide`
- **Rationale**: Keeps the primary `README.md` clean and lightweight.
- **Alternatives Considered**: Keeping all instructions in `README.md`. This makes the README longer and less clean for agents searching for immediate project context.

## Risks / Trade-offs

- **Risk**: Out of date URLs if branch names or repository names change.
- **Mitigation**: Use the standard repository structure: `https://raw.githubusercontent.com/akatzmann/py-agent-core/main/` which matches the remote github target.
