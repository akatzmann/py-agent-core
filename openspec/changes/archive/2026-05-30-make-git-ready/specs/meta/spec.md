## ADDED Requirements

### Requirement: MIT License
The repository SHALL include a root-level LICENSE file containing the standard MIT License.

#### Scenario: Verify LICENSE file
- **WHEN** the project is inspected at the root directory
- **THEN** a LICENSE file SHALL exist and contain the MIT License text.

### Requirement: Ignored env files
The repository SHALL ignore `.env` files in git to prevent credential leaks.

#### Scenario: Verify gitignore configurations
- **WHEN** `.gitignore` is loaded
- **THEN** it SHALL contain a rule to ignore `.env` files.

### Requirement: Comprehensive README documentation
The repository SHALL include a comprehensive `README.md` at the root explaining setup, usage, and backends.

#### Scenario: Verify README file
- **WHEN** the project is inspected at the root directory
- **THEN** a README.md file SHALL exist and contain installation and quickstart documentation.
