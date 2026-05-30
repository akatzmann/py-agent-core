import pytest
import asyncio
from py_agent_core.agent import PyAgent, AgentEvent
from py_agent_core.backends.dummy import DummyBackend
from py_agent_core.tool import tool

@pytest.mark.asyncio
async def test_agent_text_only():
    backend = DummyBackend(lorem_text="hello world", chunk_delay=0.0)
    agent = PyAgent(backend, system_prompt="You are helpful.")
    
    events = []
    async for event in agent.run_loop("say something"):
        events.append(event)
        
    assert events[0].type == "text_delta"
    assert events[0].content == "hello "
    assert events[1].type == "text_delta"
    assert events[1].content == "world"
    assert events[2].type == "done"
    assert events[2].content == "hello world"

@pytest.mark.asyncio
async def test_agent_with_tool_execution():
    backend = DummyBackend(chunk_delay=0.0)
    
    @tool
    def get_weather(location: str) -> str:
        return f"Weather in {location} is sunny."
        
    agent = PyAgent(backend, system_prompt="You are helpful.", tools=[get_weather])
    
    events = []
    async for event in agent.run_loop('call_tool:get_weather:{"location": "Boston"}'):
        events.append(event)
        
    # Order of events:
    # 1. tool_start
    # 2. tool_end
    # 3. text_delta (default lorem text response after feeding tool output back)
    # 4. done
    types = [e.type for e in events]
    assert "tool_start" in types
    assert "tool_end" in types
    assert "done" in types

@pytest.mark.asyncio
async def test_agent_interruption_mid_stream():
    # Simulate a stream that has a delay so we can interrupt it
    backend = DummyBackend(lorem_text="first second third", chunk_delay=0.1)
    agent = PyAgent(backend, system_prompt="You are helpful.")
    
    events = []
    
    # We will trigger the interrupt after the first text delta is received
    async def run_and_interrupt():
        async for event in agent.run_loop("speak"):
            events.append(event)
            if event.type == "text_delta":
                agent.interrupt()
                
    await run_and_interrupt()
    
    # Check that we were interrupted and did not finish generating
    types = [e.type for e in events]
    assert "interrupted" in types
    assert "done" not in types
    assert len([t for t in types if t == "text_delta"]) < 3

@pytest.mark.asyncio
async def test_agent_ollama_invalid_arguments_recovery():
    from unittest.mock import AsyncMock, MagicMock
    from py_agent_core.backends.ollama import OllamaBackend
    
    @tool
    def read_file(path: str) -> str:
        return f"Content of {path}"
        
    mock_client = MagicMock()
    
    # We want mock_client.chat to behave differently on the first and second call:
    # First call: return a tool call chunk with list arguments: '["path1.txt", "path2.txt"]'
    # Second call: return a final text response chunk: "I encountered an error."
    call_count = 0
    async def mock_chat_stream(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        async def stream_gen():
            if call_count == 1:
                # First call: yield a tool call chunk
                # Ollama SDK returns tool calls as dictionaries under message["tool_calls"]
                yield {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call_mock_1",
                                "type": "function",
                                "function": {
                                    "name": "read_file",
                                    "arguments": ["path1.txt", "path2.txt"] # List type returned by Ollama server
                                }
                            }
                        ]
                    }
                }
            else:
                # Second call: yield final text content
                yield {
                    "message": {
                        "role": "assistant",
                        "content": "I got an error from the tool because of invalid arguments.",
                        "tool_calls": None
                    }
                }
                
        return stream_gen()
        
    mock_client.chat = AsyncMock(side_effect=mock_chat_stream)
    
    backend = OllamaBackend(client=mock_client, model="llama3")
    agent = PyAgent(backend, system_prompt="You are helpful.", tools=[read_file])
    
    events = []
    async for event in agent.run_loop("read the files"):
        events.append(event)
        
    # Let's verify the flow of events:
    # 1. tool_start (for read_file)
    # 2. tool_end (delivering result)
    # 3. text_delta (for final message)
    # 4. done (for final message content)
    types = [e.type for e in events]
    assert "tool_start" in types
    assert "tool_end" in types
    assert "done" in types
    
    # Verify the done event content from the second turn was received
    done_event = next(e for e in events if e.type == "done")
    assert "I got an error from the tool" in done_event.content
