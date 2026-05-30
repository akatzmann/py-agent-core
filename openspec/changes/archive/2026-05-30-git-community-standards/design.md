## Context

To establish high standards of repo health and community collaboration, we need to create standard contributing, code of conduct, security reporting, and issue templates. 

## Goals / Non-Goals

**Goals:**
- Provide a clear, actionable guide for contributors setting up their local dev environment and running tests.
- Formulate a Code of Conduct to outline community expectations.
- Design a Security Policy defining vulnerability disclosure channels.
- Set up YAML-based GitHub issue forms to standardize incoming bugs and features.

**Non-Goals:**
- Documenting deployment credentials or internal release guidelines.
- Changing any source code behavior.

## Decisions

### Decision 1: Issue template format
- **Alternative 1:** Standard markdown templates (.md). (Rejected: Users often delete or ignore template sections, leading to messy, incomplete issues).
- **Alternative 2:** GitHub YAML issue forms (.yml). (Chosen: Renders structured, form-based inputs on GitHub, enforcing validations and mandatory fields for bug reports).

### Decision 2: Code of Conduct selection
- **Alternative 1:** Custom written code of conduct. (Rejected: High legal and operational overhead).
- **Alternative 2:** Contributor Covenant v2.1. (Chosen: The industry standard used by thousands of open source projects; widely understood and accepted).

### Decision 3: Contributing instructions scope
- **Alternative 1:** Re-documenting the full setup guide. (Rejected: Creates duplicate docs which can go stale).
- **Alternative 2:** Directing contributors to use python virtualenvs, pytest commands, and referencing `docs/guide/installation.md`. (Chosen: Keeps `CONTRIBUTING.md` focused on contribution flows while avoiding documentation duplication).

## Risks / Trade-offs

- **Template Overhead:** Forms might be slightly more tedious to fill out. (Mitigation: Keep form fields minimal and only require critical information like steps-to-reproduce and environment details).
