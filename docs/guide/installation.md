# Installation Guide

## Direct Installation (Using pip)

To install `py-agent-core` directly into your Python environment from the repository:

```bash
pip install git+https://github.com/akatzmann/py-agent-core.git
```

## Local Development Setup

To clone the repository and set up a local development environment:

```bash
# Clone the repository
git clone https://github.com/akatzmann/py-agent-core.git
cd py-agent-core

# Set up a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package with test dependencies
pip install -e ".[test]"
```

After installation, verify everything is functional by running the test suite:
```bash
PYTHONPATH=. pytest
```

