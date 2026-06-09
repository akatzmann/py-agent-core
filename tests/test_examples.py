import pytest
import asyncio
from unittest.mock import patch, MagicMock
from examples.hierarchical_assistant import main as assistant_main
from examples.search_watchdog import main as watchdog_main
from examples.structured_streaming import main as structured_main
from examples.rhetoric_speaker import speaker_loop
from examples.utils import get_backend_from_args
from py_agent_core import (
    OllamaBackend,
    AzureOpenAIBackend,
    DummyBackend,
    Agent,
    MessageUpdateEvent,
    AgentEndEvent,
    InterruptedEvent
)
from examples.interactive_chat import build_tui
from examples.guardrail_streaming import guardrail_filter
from examples.agent_swarm import main as swarm_main
from examples.self_healing_coder import main as coder_main, execute_python_code
from examples.hello_agent import main as hello_main
from examples.advanced_agent_features import main as advanced_main
from examples.background_tool import main as background_main


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
            agent_context["agent"].abort()
            
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

@pytest.mark.asyncio
async def test_interactive_chat_tui_build():
    with patch("sys.argv", ["examples/interactive_chat.py"]):
        app = build_tui()
        assert app is not None
        assert app.layout is not None

@pytest.mark.asyncio
async def test_guardrail_streaming_masking_and_preemption():
    backend = DummyBackend()
    agent = Agent(backend, initial_state={"systemPrompt": "test"})
    
    # Mock active_run for testing abort() in isolation
    from py_agent_core.agent import ActiveRun
    from py_agent_core.agent_loop import AbortSignal
    agent.active_run = ActiveRun(task=MagicMock(), abort_signal=AbortSignal())
    
    # 1. Test PII masking
    async def mock_stream_pii():
        yield MessageUpdateEvent(message={}, assistant_message_event={"type": "text_delta", "delta": "Contact john"})
        yield MessageUpdateEvent(message={}, assistant_message_event={"type": "text_delta", "delta": "@example.com"})
        yield MessageUpdateEvent(message={}, assistant_message_event={"type": "text_delta", "delta": " now."})
        yield AgentEndEvent(messages=[{"role": "assistant", "content": "Contact john@example.com now."}])
        
    filtered_events = []
    async for event in guardrail_filter(mock_stream_pii(), agent):
        filtered_events.append(event)
        
    text_deltas = "".join(
        e.assistant_message_event["delta"]
        for e in filtered_events
        if e.type == "message_update" and e.assistant_message_event.get("type") == "text_delta"
    )
    assert "[REDACTED_EMAIL]" in text_deltas
    assert "john@example.com" not in text_deltas

    # 2. Test preemption on blocked keyword
    async def mock_stream_blocked():
        yield MessageUpdateEvent(message={}, assistant_message_event={"type": "text_delta", "delta": "Here is "})
        yield MessageUpdateEvent(message={}, assistant_message_event={"type": "text_delta", "delta": "toxic_keyword"})
        yield MessageUpdateEvent(message={}, assistant_message_event={"type": "text_delta", "delta": " and more text."})
        yield AgentEndEvent(messages=[{"role": "assistant", "content": "Here is toxic_keyword and more text."}])
        
    filtered_events = []
    async for event in guardrail_filter(mock_stream_blocked(), agent):
        filtered_events.append(event)
        
    assert agent.active_run.abort_signal.aborted is True
    interrupted_events = [e for e in filtered_events if e.type == "interrupted"]
    assert len(interrupted_events) == 1
    assert "Blocked content detected" in interrupted_events[0].reason

@pytest.mark.asyncio
async def test_agent_swarm_example():
    with patch("sys.argv", ["examples/agent_swarm.py"]):
        await swarm_main()

@pytest.mark.asyncio
async def test_self_healing_coder_example_and_tool():
    # Test tool directly with valid code
    res_success = await execute_python_code('print("Hello from subprocess")')
    assert "Execution Succeeded" in res_success
    assert "Hello from subprocess" in res_success
    
    # Test tool directly with syntax error code
    res_fail = await execute_python_code('print("Hello from subprocess')
    assert "failed" in res_fail.lower()
    assert "Traceback" in res_fail or "Error" in res_fail
    
    # Run full self-healing main demo
    with patch("sys.argv", ["examples/self_healing_coder.py"]):
        await coder_main()

@pytest.mark.asyncio
async def test_hello_agent_example():
    with patch("sys.argv", ["examples/hello_agent.py"]):
        await hello_main()

@pytest.mark.asyncio
async def test_advanced_features_example():
    with patch("sys.argv", ["examples/advanced_agent_features.py", "--non-interactive", "--backend", "dummy"]):
        await advanced_main()

@pytest.mark.asyncio
async def test_background_tool_example():
    with patch("sys.argv", ["examples/background_tool.py"]):
        await background_main()

