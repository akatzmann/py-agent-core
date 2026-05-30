## Context

Currently, the executable examples in the `examples/` directory have hardcoded mock backends (`DummyBackend`). This design establishes a reusable command-line utility to let developers point any example script to live local Ollama instances or Azure OpenAI services.

## Goals / Non-Goals

**Goals:**
- Provide a standardized, reusable argument parser helper in `examples/utils.py`.
- Support specifying backend class, model name, endpoint URL, and API key via CLI flags.
- Refactor all 4 existing example scripts to use this parser helper and dynamically select the backend.

**Non-Goals:**
- Modifying core library code in `py_agent_core/`.
- Adding interactive configuration wizards or file-based configuration profiles (e.g., config.ini/dotenv).

## Decisions

### 1. Reusable Parsing Helper
- **Option A (Chosen):** Create a shared module `examples/utils.py` containing a function `get_backend_from_args()`. It uses `argparse` to parse arguments and returns an initialized backend instance along with the model name.
- **Option B:** Copy/paste `argparse` configuration blocks inside each of the 4 examples independently.
- **Rationale:** Option A avoids code duplication and ensures a consistent interface across all examples.

## Argparse Spec

The helper in `examples/utils.py` will define:
```python
import argparse
from py_agent_core import DummyBackend, OllamaBackend, AzureOpenAIBackend
from ollama import AsyncClient
from openai import AsyncAzureOpenAI

def get_backend_from_args() -> tuple[BaseBackend, str]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["dummy", "ollama", "azure"], default="dummy")
    parser.add_argument("--model", type=str, default="llama3")
    parser.add_argument("--endpoint", type=str, default=None)
    parser.add_argument("--api-key", type=str, default=None)
    
    args, _ = parser.parse_known_args()
    
    if args.backend == "ollama":
        client = AsyncClient(host=args.endpoint) if args.endpoint else None
        return OllamaBackend(client=client, model=args.model), args.model
    elif args.backend == "azure":
        client = AsyncAzureOpenAI(
            api_key=args.api_key or "MOCK_KEY",
            azure_endpoint=args.endpoint or "https://mock.azure.com",
            api_version="2024-02-15-preview"
        )
        return AzureOpenAIBackend(client=client, model=args.model), args.model
    else:
        return DummyBackend(), args.model
```

## Risks / Trade-offs

- **[Risk] Missing API keys or incorrect endpoints** → *Mitigation:* Supply fallback/mock credentials in argparse translation so the client doesn't crash on instantiation, but throws clear errors if executed.
