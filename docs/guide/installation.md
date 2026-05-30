# Installation Guide

To install and set up `py-agent-core`, run the following commands in your terminal:

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
