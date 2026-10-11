## 1. Packaging & Metadata Configuration

- [x] 1.1 Update `pyproject.toml` with `name = "python-agent-core"`, author information, repository URLs, classifiers, and keywords.
- [x] 1.2 Create `py_agent_core/py.typed` marker for PEP 561 typing support.
- [x] 1.3 Remove legacy `setup.py` and verify `.gitignore` includes `build/` and `dist/`.

## 2. GitHub Actions CI/CD Pipeline

- [x] 2.1 Create `.github/workflows/publish.yml` with PyPI Trusted Publishing (OIDC) permissions (`id-token: write`) and `pypa/gh-action-pypi-publish`.
- [x] 2.2 Test build generation locally (`python -m build`) and verify package integrity using `twine check`.

## 3. Documentation Updates & Verification

- [x] 3.1 Update `README.md` to reference `pip install python-agent-core` and include PyPI badges.
- [x] 3.2 Update `docs/guide/installation.md` with the PyPI installation commands.
- [x] 3.3 Execute test suite to confirm package discovery and full test pass.
