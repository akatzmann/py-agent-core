import pytest
from unittest.mock import AsyncMock, MagicMock
from py_agent_core.backends.dummy import DummyBackend
from py_agent_core.backends.ollama import OllamaBackend

@pytest.mark.asyncio
async def test_dummy_backend_text():
    backend = DummyBackend(lorem_text="hello world test", chunk_delay=0.0)
    messages = [{"role": "user", "content": "speak"}]
    
    chunks = []
    async for chunk in backend.generate_stream(messages):
        chunks.append(chunk)
        
    assert len(chunks) == 3
    assert chunks[0].text == "hello "
    assert chunks[1].text == "world "
    assert chunks[2].text == "test"

@pytest.mark.asyncio
async def test_dummy_backend_tool_trigger():
    backend = DummyBackend(chunk_delay=0.0)
    messages = [{"role": "user", "content": "call_tool:get_weather:{\"location\": \"Boston\"}"}]
    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}}
            }
        }
    }]
    
    chunks = []
    async for chunk in backend.generate_stream(messages, tools=tools):
        chunks.append(chunk)
        
    assert len(chunks) == 2
    assert chunks[0].tool_calls[0].name == "get_weather"
    assert chunks[0].tool_calls[0].id == "mock_call_id"
    assert chunks[1].tool_calls[0].arguments == '{"location": "Boston"}'

@pytest.mark.asyncio
async def test_ollama_backend_robust_argument_parsing():
    # Mock the AsyncClient
    mock_client = MagicMock()
    
    # Mock the chat method to be an AsyncMock returning an empty async iterator
    async def mock_chat_stream(*args, **kwargs):
        messages = kwargs.get("messages", [])
        for msg in messages:
            if "tool_calls" in msg and msg["tool_calls"]:
                for tc in msg["tool_calls"]:
                    # Verify that arguments has been parsed/coerced to a dict
                    arguments = tc["function"]["arguments"]
                    assert isinstance(arguments, dict)
                    
        # Return an async generator that yields nothing
        async def empty_gen():
            if False:
                yield
        return empty_gen()
        
    mock_client.chat = AsyncMock(side_effect=mock_chat_stream)
    
    backend = OllamaBackend(client=mock_client, model="llama3")
    
    # 1. Valid dict string arguments
    messages_valid = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '{"path": "a.txt"}'}
                }
            ]
        }
    ]
    async for _ in backend.generate_stream(messages_valid):
        pass
        
    # 2. List arguments (invalid JSON type)
    messages_list = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_2",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '["path1.txt", "path2.txt"]'}
                }
            ]
        }
    ]
    async for _ in backend.generate_stream(messages_list):
        pass

    # 3. Invalid JSON string arguments
    messages_invalid_json = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_3",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": 'path1.txt, path2.txt'}
                }
            ]
        }
    ]
    async for _ in backend.generate_stream(messages_invalid_json):
        pass



