import pytest
from unittest.mock import AsyncMock, MagicMock
from py_agent_core.backends.dummy import DummyBackend
from py_agent_core.backends.ollama import OllamaBackend
from py_agent_core.backends.openai import OpenAIBackend

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


@pytest.mark.asyncio
async def test_ollama_backend_thinking_and_options():
    mock_client = MagicMock()
    chat_kwargs = {}
    
    async def mock_chat_stream(*args, **kwargs):
        nonlocal chat_kwargs
        chat_kwargs = kwargs
        
        async def stream_gen():
            yield {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "thinking": "Reasoning trace..."
                }
            }
            yield {
                "message": {
                    "role": "assistant",
                    "content": "Final answer.",
                    "thinking": ""
                }
            }
        return stream_gen()
        
    mock_client.chat = AsyncMock(side_effect=mock_chat_stream)
    
    backend = OllamaBackend(client=mock_client, model="deepseek-r1")
    
    messages = [
        {"role": "user", "content": "solve this"},
        {"role": "assistant", "content": "I am thinking", "thinking": "old trace"}
    ]
    
    chunks = []
    async for chunk in backend.generate_stream(messages, options={"thinking_level": "high"}):
        chunks.append(chunk)
        
    # 1. Verify think option was passed
    assert chat_kwargs.get("think") is True
    
    # 2. Verify previous thinking trace was stripped from history sent to client
    sent_messages = chat_kwargs.get("messages", [])
    assert len(sent_messages) == 2
    assert "thinking" not in sent_messages[1]
    
    # 3. Verify chunk results
    assert len(chunks) == 2
    assert chunks[0].thinking == "Reasoning trace..."
    assert chunks[0].text is None
    assert chunks[1].thinking is None
    assert chunks[1].text == "Final answer."


@pytest.mark.asyncio
async def test_openai_backend_thinking_and_options():
    mock_client = MagicMock()
    create_kwargs = {}
    
    # Mock choices with delta content and reasoning_content
    mock_choice_1 = MagicMock()
    mock_choice_1.delta = MagicMock(content=None, reasoning_content="Thinking trace...", tool_calls=None)
    mock_chunk_1 = MagicMock(choices=[mock_choice_1])
    
    mock_choice_2 = MagicMock()
    mock_choice_2.delta = MagicMock(content="Final answer.", reasoning_content=None, tool_calls=None)
    mock_chunk_2 = MagicMock(choices=[mock_choice_2])

    class MockStream:
        def __init__(self, items):
            self.items = items
        def __aiter__(self):
            return self
        async def __anext__(self):
            if not self.items:
                raise StopAsyncIteration
            return self.items.pop(0)
        async def close(self):
            pass

    async def mock_create(*args, **kwargs):
        nonlocal create_kwargs
        create_kwargs = kwargs
        return MockStream([mock_chunk_1, mock_chunk_2])
        
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=mock_create)
    
    backend = OpenAIBackend(client=mock_client, model="o1-mini")
    
    messages = [
        {"role": "user", "content": "solve this"},
        {"role": "assistant", "content": "I am thinking", "thinking": "old trace"}
    ]
    
    chunks = []
    async for chunk in backend.generate_stream(messages, options={"thinking_level": "medium"}):
        chunks.append(chunk)
        
    # 1. Verify reasoning_effort option was passed
    assert create_kwargs.get("reasoning_effort") == "medium"
    
    # 2. Verify previous thinking trace was stripped from history sent to client (via sanitization)
    sent_messages = create_kwargs.get("messages", [])
    assert len(sent_messages) == 2
    assert "thinking" not in sent_messages[1]
    
    # 3. Verify chunk results
    assert len(chunks) == 2
    assert chunks[0].thinking == "Thinking trace..."
    assert chunks[0].text is None
    assert chunks[1].thinking is None
    assert chunks[1].text == "Final answer."


@pytest.mark.asyncio
async def test_openai_backend_non_reasoning_model():
    mock_client = MagicMock()
    create_kwargs = {}
    
    mock_choice = MagicMock()
    mock_choice.delta = MagicMock(content="Hello", reasoning_content=None, tool_calls=None)
    mock_chunk = MagicMock(choices=[mock_choice])

    class MockStream:
        def __init__(self, items):
            self.items = items
        def __aiter__(self):
            return self
        async def __anext__(self):
            if not self.items:
                raise StopAsyncIteration
            return self.items.pop(0)
        async def close(self):
            pass

    async def mock_create(*args, **kwargs):
        nonlocal create_kwargs
        create_kwargs = kwargs
        return MockStream([mock_chunk])
        
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=mock_create)
    
    backend = OpenAIBackend(client=mock_client, model="gpt-4o")
    messages = [{"role": "user", "content": "hello"}]
    
    chunks = []
    async for chunk in backend.generate_stream(messages, options={"thinking_level": "medium"}):
        chunks.append(chunk)
        
    assert "reasoning_effort" not in create_kwargs
    assert chunks[0].text == "Hello"


@pytest.mark.asyncio
async def test_backend_sampling_parameters():
    # 1. Test BaseBackend attributes storing
    from py_agent_core.backends.base import BaseBackend
    class TestBackend(BaseBackend):
        async def generate_stream(self, messages, tools=None, options=None):
            pass
    tb = TestBackend(temperature=0.5, top_p=0.8)
    assert tb.temperature == 0.5
    assert tb.top_p == 0.8

    # 2. Test OpenAIBackend forwarding
    mock_client = MagicMock()
    create_kwargs = {}
    mock_choice = MagicMock()
    mock_choice.delta = MagicMock(content="Hello", reasoning_content=None, tool_calls=None)
    mock_chunk = MagicMock(choices=[mock_choice])

    class MockStream:
        def __init__(self, items):
            self.items = items
        def __aiter__(self):
            return self
        async def __anext__(self):
            if not self.items:
                raise StopAsyncIteration
            return self.items.pop(0)
        async def close(self):
            pass

    async def mock_create(*args, **kwargs):
        nonlocal create_kwargs
        create_kwargs = kwargs
        return MockStream([mock_chunk])

    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=mock_create)

    openai_backend = OpenAIBackend(client=mock_client, model="gpt-4o", temperature=0.7, top_p=0.9)
    assert openai_backend.temperature == 0.7
    assert openai_backend.top_p == 0.9

    async for _ in openai_backend.generate_stream([{"role": "user", "content": "hello"}]):
        pass

    assert create_kwargs.get("temperature") == 0.7
    assert create_kwargs.get("top_p") == 0.9

    # 3. Test OllamaBackend forwarding
    mock_client_ollama = MagicMock()
    chat_kwargs = {}
    async def mock_chat_stream(*args, **kwargs):
        nonlocal chat_kwargs
        chat_kwargs = kwargs
        async def stream_gen():
            yield {"message": {"role": "assistant", "content": "Hello"}}
            if False:
                yield
        return stream_gen()

    mock_client_ollama.chat = AsyncMock(side_effect=mock_chat_stream)
    ollama_backend = OllamaBackend(client=mock_client_ollama, model="llama3", temperature=0.4, top_p=0.85)
    assert ollama_backend.temperature == 0.4
    assert ollama_backend.top_p == 0.85

    async for _ in ollama_backend.generate_stream([{"role": "user", "content": "hello"}]):
        pass

    options_sent = chat_kwargs.get("options", {})
    assert options_sent.get("temperature") == 0.4
    assert options_sent.get("top_p") == 0.85





