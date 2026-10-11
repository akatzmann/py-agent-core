## Why

The `py-agent-core` library currently requires installation directly from git source (`pip install git+https://...`). To make the library easily discoverable, versioned, and installable by the broader Python community via `pip install python-agent-core`, the project needs proper PyPI packaging and automated release publishing. Since the name `py-agent-core` on PyPI is occupied by an abandoned placeholder, the library is being published under the official name `python-agent-core` while preserving `py_agent_core` as the Python import namespace.

## What Changes

- **Package Distribution Name**: Configure `pyproject.toml` distribution name as `python-agent-core` (version `0.2.0`).
- **Packaging Metadata**: Add comprehensive PEP 621 metadata (authors, repository/issue URLs, keywords, classifiers, license, and description).
- **Type Information Support**: Add `py_agent_core/py.typed` ([PEP 561](https://peps.python.org/pep-0561/)) marker file to export typing definitions to downstream users.
- **Build Cleanliness**: Deprecate/remove legacy `setup.py` in favor of declarative `pyproject.toml` (`setuptools.build_meta`).
- **Release Automation**: Add `.github/workflows/publish.yml` using PyPI Trusted Publishing (OIDC) triggered on GitHub release events.
- **Documentation Updates**: Update `README.md` and `docs/guide/installation.md` with standard `pip install python-agent-core` commands and PyPI release badge.

## Capabilities

### New Capabilities
- `pypi-packaging`: Defines standard PEP 621 packaging metadata, PEP 561 typing declarations, wheel/sdist build configurations, and automated GitHub Actions publishing via OIDC.

### Modified Capabilities
- `meta`: Updates README and installation documentation to instruct users to install via `pip install python-agent-core` and display the PyPI version badge.

## Impact

- **Affected Files**:
  - `pyproject.toml`
  - `setup.py`
  - `py_agent_core/py.typed`
  - `.github/workflows/publish.yml`
  - `README.md`
  - `docs/guide/installation.md`
- **APIs and Runtime**: Zero breaking changes to the Python API or import paths (`from py_agent_core import ...` remains unchanged).
- **External Dependencies**: No new runtime dependencies. Requires `build` for packaging.
