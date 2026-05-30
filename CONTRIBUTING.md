# Contributing to py-agent-core

Thank you for your interest in contributing to `py-agent-core`! We welcome all contributions, from bug fixes and documentation improvements to new features and examples.

Please follow these guidelines to make the contribution process smooth and efficient.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please report any unacceptable behavior to the project maintainers.

---

## Local Development Setup

To set up a local development environment:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/akatzmann/py-agent-core.git
   cd py-agent-core
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies in editable mode**:
   Install core library and testing/development dependencies:
   ```bash
   pip install -e .[test]
   ```

---

## Running the Test Suite

We use `pytest` for all unit and integration testing. Always run the tests before submitting a pull request to ensure nothing is broken.

To run the entire test suite:
```bash
pytest
```

If you are adding new features, you must write corresponding tests in the `tests/` directory.

---

## Running the Examples

Ensure your environment is set up and run any example script from the repository root:
```bash
python -m examples.hello_agent
python -m examples.interactive_chat
```
Refer to [examples/README.md](examples/README.md) for a complete list of examples and details on swapping model backends.

---

## Pull Request Guidelines

When submitting a pull request (PR):

1. **Keep it focused**: A PR should address a single bug fix or feature.
2. **Follow PEP 8**: Ensure your Python code is clean and readable. Use descriptive variable names and write docstrings for new modules or public classes.
3. **Include type hints**: We use type hints across the project to assist with static analysis and tool schema compilation.
4. **Update documentation**: If you change public APIs or behavior, update the relevant markdown files in `docs/` and `README.md`.
5. **Pass the tests**: Ensure all tests run and pass successfully before opening the PR.

---

## Spec-Driven Development with OpenSpec

For all non-trivial changes (new features, architectural updates, or modifying core requirements), we practice **spec-driven development** using the [OpenSpec](https://github.com/Fission-AI/OpenSpec) framework. This ensures consistency and enables AI coding agents (such as Antigravity, GitHub Copilot, Claude Code, or OpenClaw) to build a clear mental model of the requirements and implement them safely.

Before starting implementation:
1. **Propose the Change**: Run `openspec new change "<change-name>"` to initialize a change workspace.
2. **Author the Specifications**: Draft the proposal, specifications (defining requirements and scenarios), and design files inside `openspec/changes/<change-name>/`.
3. **Verify and Archive**: Once implemented, run `openspec validate` and `openspec archive <change-name>` to merge specifications into the main specifications.

