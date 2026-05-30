import pytest
import asyncio
from unittest.mock import patch
from examples.hierarchical_assistant import main as assistant_main
from examples.search_watchdog import main as watchdog_main
from examples.structured_streaming import main as structured_main
from examples.rhetoric_speaker import speaker_loop
from examples.utils import get_backend_from_args
from py_agent_core import OllamaBackend, AzureOpenAIBackend, DummyBackend

@pytest.mark.asyncio
async def test_hierarchical_assistant_example():
    # Patch argv to run as default offline dummy backend
    with patch("sys.argv", ["examples/hierarchical_assistant.py"]):
        await assistant_main()

@pytest.mark.asyncio
async def test_search_watchdog_example():
    with patch("sys.argv", ["examples/search_watchdog.py"]):
        await watchdog_main()

@pytest.mark.asyncio
async def test_structured_streaming_example():
    with patch("sys.argv", ["examples/structured_streaming.py"]):
        await structured_main()

@pytest.mark.asyncio
async def test_rhetoric_speaker_example_interrupted():
    agent_context = {"agent": None, "pending_topic": None}
    
    async def trigger_interrupt():
        await asyncio.sleep(0.1)
        if agent_context["agent"]:
            agent_context["pending_topic"] = "Bird Migration"
            agent_context["agent"].interrupt()
            
    speaker_task = asyncio.create_task(
        speaker_loop(agent_context, DummyBackend(), "dummy-model")
    )
    interrupt_task = asyncio.create_task(trigger_interrupt())
    
    await asyncio.sleep(0.3)
    speaker_task.cancel()
    interrupt_task.cancel()
    
    try:
        await speaker_task
    except asyncio.CancelledError:
        pass
        
    assert agent_context["agent"] is not None

def test_cli_backend_parsing_ollama():
    test_args = ["prog_name", "--backend", "ollama", "--model", "qwen", "--endpoint", "http://localhost:11434"]
    with patch("sys.argv", test_args):
        backend, model = get_backend_from_args()
        assert isinstance(backend, OllamaBackend)
        assert model == "qwen"
        assert backend.model == "qwen"

def test_cli_backend_parsing_azure():
    test_args = ["prog_name", "--backend", "azure", "--model", "gpt-4", "--api-key", "secret"]
    with patch("sys.argv", test_args):
        backend, model = get_backend_from_args()
        assert isinstance(backend, AzureOpenAIBackend)
        assert model == "gpt-4"
        assert backend.model == "gpt-4"

def test_cli_backend_parsing_dummy():
    test_args = ["prog_name", "--backend", "dummy"]
    with patch("sys.argv", test_args):
        backend, model = get_backend_from_args()
        assert isinstance(backend, DummyBackend)
