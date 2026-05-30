import argparse
from typing import Tuple
from py_agent_core import BaseBackend, DummyBackend, OllamaBackend, AzureOpenAIBackend
from ollama import AsyncClient
from openai import AsyncAzureOpenAI

def get_backend_from_args(description: str = "PyAgent Example") -> Tuple[BaseBackend, str]:
    """Parses standard command-line arguments to resolve and return an LLM backend and model name."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--backend", choices=["dummy", "ollama", "azure"], default="dummy",
                        help="LLM backend adapter to use (default: dummy)")
    parser.add_argument("--model", type=str, default="llama3",
                        help="Model identifier or deployment name (default: llama3)")
    parser.add_argument("--endpoint", type=str, default=None,
                        help="Model backend endpoint URL (e.g. http://host.containers.internal:11434 for Ollama)")
    parser.add_argument("--api-key", type=str, default=None,
                        help="API authentication key (required for Azure OpenAI)")

    args, _ = parser.parse_known_args()

    if args.backend == "ollama":
        client = AsyncClient(host=args.endpoint) if args.endpoint else None
        return OllamaBackend(client=client, model=args.model), args.model
    elif args.backend == "azure":
        # Supply a placeholder or check
        client = AsyncAzureOpenAI(
            api_key=args.api_key or "MOCK_AZURE_KEY",
            azure_endpoint=args.endpoint or "https://mock-azure-endpoint.openai.azure.com",
            api_version="2024-02-15-preview"
        )
        return AzureOpenAIBackend(client=client, model=args.model), args.model
    else:
        return DummyBackend(), args.model
