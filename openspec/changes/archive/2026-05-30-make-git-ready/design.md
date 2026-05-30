## Context

Before releasing `py-agent-core` on GitHub, we need to establish standard open-source documentation, add the MIT License matching our package configuration, and prevent local environment files (`.env`) from being committed.

## Goals / Non-Goals

**Goals:**
- Add `.env` to `.gitignore`.
- Add MIT `LICENSE`.
- Provide a robust, clean `README.md` explaining installation, quickstart, tool usage, and testing.

**Non-Goals:**
- Changing package configurations or requirements inside `pyproject.toml` or `setup.py`.

## Decisions

### Decision 1: Create standard LICENSE file matching package metadata
We will add a root `LICENSE` file containing the standard MIT License.
- *Rationale*: Confirms the OSI MIT License specified in `pyproject.toml` for compliance.

### Decision 2: Update README with comprehensive API usage
We will replace the brief `README.md` with a detailed one.
- *Rationale*: Makes the project easy to adopt by providing setup, backend configurations, and clear examples of tool decoration and custom event loop.

## Risks / Trade-offs

No technical risks.
