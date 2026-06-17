from py_agent_core.agent import PyAgent, AgentEventCompat, Agent
from py_agent_core.tool import tool
from py_agent_core.agent_loop import (
    agent_loop,
    agent_loop_continue,
    AgentContext,
    AgentLoopConfig,
    AgentLoopTurnUpdate,
    AgentEvent,
    AgentStartEvent,
    AgentEndEvent,
    TurnStartEvent,
    TurnEndEvent,
    MessageStartEvent,
    MessageUpdateEvent,
    MessageEndEvent,
    ToolExecutionStartEvent,
    ToolExecutionUpdateEvent,
    ToolExecutionEndEvent,
    InterruptedEvent,
    ErrorEvent
)
from py_agent_core.backends.base import BaseBackend, BackendChunk
from py_agent_core.backends.azure_openai import AzureOpenAIBackend
from py_agent_core.backends.openai import OpenAIBackend
from py_agent_core.backends.ollama import OllamaBackend
from py_agent_core.backends.dummy import DummyBackend

# For legacy mapping compatibility
AgentEvent = AgentEventCompat

__all__ = [
    "PyAgent",
    "AgentEvent",
    "Agent",
    "tool",
    "agent_loop",
    "agent_loop_continue",
    "AgentContext",
    "AgentLoopConfig",
    "AgentLoopTurnUpdate",
    "AgentStartEvent",
    "AgentEndEvent",
    "TurnStartEvent",
    "TurnEndEvent",
    "MessageStartEvent",
    "MessageUpdateEvent",
    "MessageEndEvent",
    "ToolExecutionStartEvent",
    "ToolExecutionUpdateEvent",
    "ToolExecutionEndEvent",
    "InterruptedEvent",
    "ErrorEvent",
    "BaseBackend",
    "BackendChunk",
    "AzureOpenAIBackend",
    "OpenAIBackend",
    "OllamaBackend",
    "DummyBackend",
]
