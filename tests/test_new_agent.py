import pytest
import asyncio
import time
from typing import List, Dict, Any, Optional
from py_agent_core import (
    Agent,
    tool,
    DummyBackend,
    AgentStartEvent,
    AgentEndEvent,
    TurnStartEvent,
    TurnEndEvent,
    MessageStartEvent,
    MessageUpdateEvent,
    MessageEndEvent,
    ToolExecutionStartEvent,
    ToolExecutionEndEvent,
    InterruptedEvent,
    ErrorEvent
)

@pytest.mark.asyncio
async def test_agent_basic_events_and_state():
    backend = DummyBackend(lorem_text="Hello architecture alignment", chunk_delay=0.0)
    agent = Agent(backend=backend)
    
    events = []
    def listener(event, signal):
        events.append(event)
        
    unsubscribe = agent.subscribe(listener)
    
    # Prompt the agent
    async for event in agent.prompt_stream("Test prompt"):
        pass
        
    unsubscribe()
    
    # Verify events
    types = [e.type for e in events]
    assert "agent_start" in types
    assert "turn_start" in types
    assert "message_start" in types
    assert "message_update" in types
    assert "message_end" in types
    assert "turn_end" in types
    assert "agent_end" in types
    
    # Verify state updates
    assert len(agent.state.messages) > 0
    # The first message in history should be user prompt
    assert agent.state.messages[0]["role"] == "user"
    assert agent.state.messages[0]["content"] == "Test prompt"
    # The last message should be assistant response
    assert agent.state.messages[-1]["role"] == "assistant"
    assert agent.state.messages[-1]["content"] == "Hello architecture alignment"

@pytest.mark.asyncio
async def test_agent_parallel_execution():
    # Register two tools that sleep. If they run in parallel, total time should be close to sleep time.
    start_times = {}
    end_times = {}
    
    @tool
    async def task_one(duration: float = 0.2) -> str:
        start_times["one"] = time.time()
        await asyncio.sleep(duration)
        end_times["one"] = time.time()
        return "one done"
        
    @tool
    async def task_two(duration: float = 0.2) -> str:
        start_times["two"] = time.time()
        await asyncio.sleep(duration)
        end_times["two"] = time.time()
        return "two done"
        
    backend = DummyBackend(chunk_delay=0.0)
    agent = Agent(backend=backend, initial_state={"tools": [task_one, task_two]}, tool_execution="parallel")
    
    # Call both tools by specifying in prompt
    prompt = 'call_tool:task_one:{"duration": 0.2} and call_tool:task_two:{"duration": 0.2}'
    
    # Since DummyBackend only supports single call_tool parsing in its prompt matching,
    # let's mock generate_stream to return both tool calls concurrently.
    from unittest.mock import AsyncMock
    from py_agent_core.backends.base import BackendChunk, ToolCallChunk
    
    async def mock_generate_stream(messages, tools=None):
        if not any(m.get("role") == "tool" for m in messages):
            yield BackendChunk(tool_calls=[
                ToolCallChunk(index=0, id="c1", name="task_one", arguments='{"duration": 0.2}'),
                ToolCallChunk(index=1, id="c2", name="task_two", arguments='{"duration": 0.2}')
            ])
        else:
            yield BackendChunk(text="All tasks finished.")
        
    backend.generate_stream = mock_generate_stream
    
    t0 = time.time()
    async for event in agent.prompt_stream("run tasks"):
        pass
    t1 = time.time()
    
    # Verify parallel execution timing
    elapsed = t1 - t0
    # If sequential, elapsed would be >= 0.4 seconds. If parallel, around 0.2 seconds.
    assert elapsed < 0.35
    assert "one" in start_times and "two" in start_times
    # Verify that task_two started before task_one finished
    assert start_times["two"] < end_times["one"]
    assert start_times["one"] < end_times["two"]

@pytest.mark.asyncio
async def test_agent_sequential_execution_and_decorator():
    # Register two tools, task_one is parallel, task_two is sequential (decorated)
    start_times = {}
    end_times = {}
    
    @tool
    async def task_one(duration: float = 0.1) -> str:
        start_times["one"] = time.time()
        await asyncio.sleep(duration)
        end_times["one"] = time.time()
        return "one done"
        
    @tool(execution_mode="sequential")
    async def task_two(duration: float = 0.1) -> str:
        start_times["two"] = time.time()
        await asyncio.sleep(duration)
        end_times["two"] = time.time()
        return "two done"
        
    backend = DummyBackend(chunk_delay=0.0)
    # Even if default is parallel, task_two is sequential so execution falls back to sequential
    agent = Agent(backend=backend, initial_state={"tools": [task_one, task_two]}, tool_execution="parallel")
    
    from py_agent_core.backends.base import BackendChunk, ToolCallChunk
    async def mock_generate_stream(messages, tools=None):
        if not any(m.get("role") == "tool" for m in messages):
            yield BackendChunk(tool_calls=[
                ToolCallChunk(index=0, id="c1", name="task_one", arguments='{"duration": 0.1}'),
                ToolCallChunk(index=1, id="c2", name="task_two", arguments='{"duration": 0.1}')
            ])
        else:
            yield BackendChunk(text="All tasks finished.")
    backend.generate_stream = mock_generate_stream
    
    t0 = time.time()
    async for event in agent.prompt_stream("run tasks"):
        pass
    t1 = time.time()
    
    elapsed = t1 - t0
    # Sequential execution takes at least 0.2s
    assert elapsed >= 0.2
    # Check that they did not overlap
    assert end_times["one"] <= start_times["two"] or end_times["two"] <= start_times["one"]

@pytest.mark.asyncio
async def test_before_tool_call_hook_blocking():
    @tool
    def secret_tool() -> str:
        return "top secret info"
        
    blocked_calls = []
    
    async def before_hook(data, signal):
        if data["tool_call"]["function"]["name"] == "secret_tool":
            blocked_calls.append(data)
            return {"block": True, "reason": "Access Denied"}
        return None
        
    backend = DummyBackend(chunk_delay=0.0)
    agent = Agent(backend=backend, initial_state={"tools": [secret_tool]}, before_tool_call=before_hook)
    
    from py_agent_core.backends.base import BackendChunk, ToolCallChunk
    async def mock_generate_stream(messages, tools=None):
        # First turn: call tool
        if not any(m.get("role") == "tool" for m in messages):
            yield BackendChunk(tool_calls=[
                ToolCallChunk(index=0, id="c1", name="secret_tool", arguments="{}")
            ])
        else:
            yield BackendChunk(text="Finished.")
    backend.generate_stream = mock_generate_stream
    
    async for event in agent.prompt_stream("call secret tool"):
        pass
        
    assert len(blocked_calls) == 1
    # Check that the tool result contains the block reason in history
    tool_results = [m for m in agent.state.messages if m.get("role") == "toolResult"]
    assert len(tool_results) == 1
    assert "Access Denied" in str(tool_results[0]["content"])

@pytest.mark.asyncio
async def test_after_tool_call_hook_rewriting_and_termination():
    @tool
    def simple_tool() -> str:
        return "original result"
        
    async def after_hook(data, signal):
        # Modify the content and terminate early
        return {
            "content": [{"type": "text", "text": "rewritten result"}],
            "terminate": True
        }
        
    backend = DummyBackend(chunk_delay=0.0)
    agent = Agent(backend=backend, initial_state={"tools": [simple_tool]}, after_tool_call=after_hook)
    
    from py_agent_core.backends.base import BackendChunk, ToolCallChunk
    called_turns = 0
    async def mock_generate_stream(messages, tools=None):
        nonlocal called_turns
        called_turns += 1
        yield BackendChunk(tool_calls=[
            ToolCallChunk(index=0, id="c1", name="simple_tool", arguments="{}")
        ])
    backend.generate_stream = mock_generate_stream
    
    async for event in agent.prompt_stream("call simple tool"):
        pass
        
    # Check that LLM was only called once, and didn't follow up since terminate=True was returned by after_hook
    assert called_turns == 1
    
    # Check that history contains the rewritten result
    tool_results = [m for m in agent.state.messages if m.get("role") == "toolResult"]
    assert len(tool_results) == 1
    assert "rewritten result" in str(tool_results[0]["content"])

@pytest.mark.asyncio
async def test_context_pipelines_hooks():
    # Test convert_to_llm and transform_context
    transformed = False
    converted = False
    
    def transform_ctx(messages, signal):
        nonlocal transformed
        transformed = True
        # Let's add an extra header to messages
        return [{"role": "system", "content": "Transformed System Prompt"}] + messages
        
    def convert_llm(messages):
        nonlocal converted
        converted = True
        # Add a sentinel to make sure the backend sees it
        return [{"role": "user", "content": "sentinel"}]
        
    backend = DummyBackend(chunk_delay=0.0)
    
    received_messages_by_backend = None
    async def mock_generate_stream(messages, tools=None):
        nonlocal received_messages_by_backend
        received_messages_by_backend = messages
        yield BackendChunk(text="done")
    backend.generate_stream = mock_generate_stream
    
    agent = Agent(
        backend=backend,
        transform_context=transform_ctx,
        convert_to_llm=convert_llm
    )
    
    async for event in agent.prompt_stream("hello"):
        pass
        
    assert transformed is True
    assert converted is True
    assert received_messages_by_backend == [{"role": "user", "content": "sentinel"}]

@pytest.mark.asyncio
async def test_steering_and_follow_up_queues():
    backend = DummyBackend(chunk_delay=0.0)
    agent = Agent(backend=backend)
    
    # Test steering queue mid-run
    # We will simulate steering inside a subscription listener when we see a message start event
    steered = False
    def listener(event, signal):
        nonlocal steered
        if event.type == "message_start" and event.message.get("role") == "assistant" and not steered:
            agent.steer({"role": "user", "content": "steering msg", "timestamp": int(time.time()*1000)})
            steered = True
            
    agent.subscribe(listener)
    
    # We also queue a follow-up message before we start
    agent.follow_up({"role": "user", "content": "follow-up msg", "timestamp": int(time.time()*1000)})
    
    # Run the prompt
    async for event in agent.prompt_stream("start run"):
        pass
        
    # Verify that steering message and follow-up message are both in the history
    history_roles_contents = [(m["role"], m.get("content")) for m in agent.state.messages]
    
    # It should look like:
    # 1. user: start run
    # 2. assistant: response
    # 3. user: steering msg (steered mid-run)
    # 4. assistant: response
    # 5. user: follow-up msg (run after current turn idle)
    # 6. assistant: response
    
    assert ("user", "steering msg") in history_roles_contents
    assert ("user", "follow-up msg") in history_roles_contents

@pytest.mark.asyncio
async def test_turn_transition_hooks():
    # should_stop_after_turn and prepare_next_turn
    next_turn_prepared = False
    
    def prep_next(context):
        nonlocal next_turn_prepared
        next_turn_prepared = True
        return None
        
    stop_called = 0
    def should_stop(context):
        nonlocal stop_called
        stop_called += 1
        return True # Stop immediately after the first turn
        
    backend = DummyBackend(chunk_delay=0.0)
    agent = Agent(
        backend=backend,
        prepare_next_turn=prep_next,
        should_stop_after_turn=should_stop
    )
    
    # Set up a tool call that would normally trigger a second turn
    @tool
    def simple_tool() -> str:
        return "res"
        
    agent.state.tools = [simple_tool]
    
    from py_agent_core.backends.base import BackendChunk, ToolCallChunk
    async def mock_generate_stream(messages, tools=None):
        if not any(m.get("role") == "tool" for m in messages):
            yield BackendChunk(tool_calls=[
                ToolCallChunk(index=0, id="c1", name="simple_tool", arguments="{}")
            ])
        else:
            yield BackendChunk(text="Finished.")
    backend.generate_stream = mock_generate_stream
    
    async for event in agent.prompt_stream("trigger tool"):
        pass
        
    assert next_turn_prepared is True
    assert stop_called == 1
    # Check that loop stopped before calling LLM again (no assistant messages in history other than tool result)
    # Wait, the history will have the tool result
    tool_results = [m for m in agent.state.messages if m.get("role") == "toolResult"]
    assert len(tool_results) == 1
