## Why

In the era of agent-driven development, developers use tools like Antigravity, Claude Code, OpenClaw, OpenCode, and GitHub Copilot to read, explain, and setup codebases. Providing a standard long-form README makes humans do manual work and delays agent ingestion. By creating agent-optimized readme sections and a dedicated installation guide, we reduce friction and enable agents to configure the project automatically.

## What Changes

- Add a "Skip Reading This Readme" context-delegation section at the beginning of `README.md`.
- Extract detailed installation instructions into a new `docs/guide/installation.md` file.
- Update the `README.md` `Installation` section to guide humans and LLM agents on how to install and setup the project using raw URLs and curl.

## Capabilities

### New Capabilities

### Modified Capabilities
- `meta`: Update README.md and add installation.md under docs/guide to introduce agentic documentation context delegation.

## Impact

This is a documentation-only change. It does not affect Python source code, APIs, or project dependencies.
