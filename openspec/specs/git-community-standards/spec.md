# git-community-standards Specification

## Purpose
TBD - created by archiving change git-community-standards. Update Purpose after archive.
## Requirements
### Requirement: Repository Contributing Guidelines
The repository SHALL contain a CONTRIBUTING.md file in the root directory that defines environment setup, code style constraints, and pull request procedures.

#### Scenario: Developer checks contributing instructions
- **WHEN** a contributor views CONTRIBUTING.md
- **THEN** they SHALL find instructions for setting up the virtualenv, running tests, and creating pull requests.

### Requirement: Repository Code of Conduct
The repository SHALL contain a CODE_OF_CONDUCT.md file in the root directory that adopts the standard Contributor Covenant code of conduct.

#### Scenario: Community member views code of conduct
- **WHEN** a community member views CODE_OF_CONDUCT.md
- **THEN** they SHALL find the pledge, standards, responsibilities, and enforcement mechanisms.

### Requirement: Repository Security Policy
The repository SHALL contain a SECURITY.md file in the root directory detailing vulnerability reporting instructions and supported versions.

#### Scenario: Security researcher reports a vulnerability
- **WHEN** a researcher reads SECURITY.md
- **THEN** they SHALL find instructions on where and how to securely disclose potential vulnerabilities.

### Requirement: GitHub Issue Templates
The repository SHALL contain YAML-based GitHub issue forms under .github/ISSUE_TEMPLATE/ for bug reports and feature requests.

#### Scenario: User opens a new bug report on GitHub
- **WHEN** a user selects the bug report template on GitHub
- **THEN** they SHALL be presented with structured fields for description, steps to reproduce, expected behavior, and environment info.

