## Why

To establish the project as a mature open-source repository and encourage community participation, we need standard Git repository health files. Currently, the repository lacks contributing guidelines, a code of conduct, vulnerability disclosure guidelines, and structured issue templates, which increases friction for external contributors.

## What Changes

We will introduce several standard repository templates and documents to align with Open Source and Git community standards:
- `CONTRIBUTING.md`: Outlines developer workspace setup, code styling rules, and how to submit bug fixes or features.
- `CODE_OF_CONDUCT.md`: Standard Contributor Covenant Code of Conduct for community safety.
- `SECURITY.md`: Instructions for reporting security vulnerabilities (crucial given our subprocess interpreter example).
- `.github/ISSUE_TEMPLATE/bug_report.yml` and `feature_request.yml`: Structured YAML issue forms for structured issue logging.

## Capabilities

### New Capabilities
- `git-community-standards`: New community health documentation and templates including Code of Conduct, Contributing rules, Security procedures, and GitHub Issue forms.

### Modified Capabilities

## Impact

This change introduces new non-functional documentation files and GitHub configuration. It has zero impact on core library execution, APIs, or existing project dependencies.
