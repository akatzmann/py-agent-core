# pypi-packaging Specification

## Purpose
Defines distribution metadata, type declarations, build configurations, and automated OIDC-based PyPI release publishing for python-agent-core.

## Requirements
### Requirement: PyPI Packaging Configuration
The package configuration in `pyproject.toml` SHALL declare the project distribution name as `python-agent-core`, specify the import package directory as `py_agent_core`, and define standard PEP 621 metadata including authors, repository/issue URLs, keywords, and classifiers.

#### Scenario: Build wheel and source distributions
- **WHEN** `python -m build` is executed on the repository
- **THEN** it SHALL produce valid `.whl` and `.tar.gz` distribution archives under `dist/` with package name `python_agent_core`.

### Requirement: Type Hint Marker
The library package SHALL include an empty `py.typed` marker file at `py_agent_core/py.typed` adhering to PEP 561 to declare inline typing support for downstream static analysis tools.

#### Scenario: Type checker inspects package
- **WHEN** a type checker or downstream application imports `py_agent_core`
- **THEN** it SHALL detect the `py.typed` marker and recognize exported type signatures from the package.

### Requirement: Automated Release Workflow
The repository SHALL define a GitHub Actions workflow at `.github/workflows/publish.yml` configured to trigger on GitHub releases and publish artifacts to PyPI using OpenID Connect (OIDC) Trusted Publishing.

#### Scenario: GitHub release triggers PyPI publishing
- **WHEN** a GitHub release is published in the repository
- **THEN** the workflow at `.github/workflows/publish.yml` SHALL execute, request an OIDC token with `id-token: write` permissions, build the distribution, and upload the artifacts to PyPI.
