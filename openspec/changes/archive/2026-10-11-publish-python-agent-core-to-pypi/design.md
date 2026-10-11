## Context

The repository currently builds via `setuptools` with a minimal `pyproject.toml` and a legacy `setup.py`. The distribution name was initially set to `py-agent-core`, but that name is held by an inactive placeholder on PyPI. The maintainer has created a pending publisher on PyPI for project `python-agent-core` bound to repository `akatzmann/py-agent-core` and workflow `publish.yml`. See [proposal.md](proposal.md) for background and motivation.

## Goals / Non-Goals

**Goals:**
- Provide full PEP 621 compliance in `pyproject.toml` with package name `python-agent-core`.
- Provide PEP 561 inline typing support via `py_agent_core/py.typed`.
- Implement automated GitHub Actions CI/CD release workflow targeting PyPI via OIDC Trusted Publishing.
- Modernize README and installation documentation to instruct `pip install python-agent-core`.
- Eliminate legacy `setup.py` in favor of declarative `pyproject.toml`.

**Non-Goals:**
- Renaming the internal Python package directory `py_agent_core` (retained to prevent breaking existing code, tests, and examples).
- Splitting provider backends (`openai`, `ollama`) into optional extras (kept in core dependencies for out-of-the-box functionality).
- Filing immediate PEP 541 reclamation dispute for `py-agent-core` (can be pursued separately out-of-band).

## Decisions

### Decision 1: Distribution name `python-agent-core` with module `py_agent_core`
- **Choice**: Publish to PyPI under `python-agent-core` while keeping the package folder `py_agent_core` intact.
- **Rationale**: Standard Python convention (`python-dotenv`, `python-dateutil`, `beautifulsoup4`). Prevents breaking existing imports, tests, and example scripts.
- **Alternatives considered**: Renaming folder to `python_agent_core` (rejected as overly verbose to import: `from python_agent_core.agent import ...`).

### Decision 2: Declarative build configuration via setuptools PEP 621
- **Choice**: Modernize `pyproject.toml` using `setuptools.build_meta` and remove `setup.py`.
- **Rationale**: Standards-compliant (PEP 517 / PEP 621). Eliminates duplicate version/name declarations.
- **Alternatives considered**: Migrating to `hatchling` or `flit-core` (unnecessary churn when `setuptools>=61.0.0` already satisfies all requirements).

### Decision 3: Trusted Publishing (OIDC) release workflow
- **Choice**: Create `.github/workflows/publish.yml` triggered on GitHub release publication (`release: types: [published]`). Use `pypa/gh-action-pypi-publish@release/v1` with `permissions: id-token: write`.
- **Rationale**: Eliminates long-lived API tokens or credentials in repository secrets. PyPI automatically links attestations and commit provenance. Matches the pending publisher configuration already registered on PyPI.
- **Alternatives considered**: Manual `twine upload` with token (rejected due to release friction and risk of dirty builds).

## Risks / Trade-offs

- **[Risk: Name mismatch between pip package and import namespace]**  
  *Mitigation*: Clearly highlight both commands in `README.md` and `docs/guide/installation.md` (`pip install python-agent-core` followed by `from py_agent_core import ...`).
- **[Risk: Workflow name or repository mismatch with PyPI Pending Publisher]**  
  *Mitigation*: Exact match for workflow file path (`.github/workflows/publish.yml`), owner (`akatzmann`), and repo (`py-agent-core`).
- **[Risk: Leftover build caches in workspace during local testing]**  
  *Mitigation*: Add `build/` and `dist/` to `.gitignore` (if not already present) and test clean build output.
