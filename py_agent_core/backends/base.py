from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, AsyncGenerator

@dataclass
class ToolCallChunk:
    index: int
    id: Optional[str] = None
    name: Optional[str] = None
    arguments: str = ""

@dataclass
class BackendChunk:
    text: Optional[str] = None
    tool_calls: Optional[List[ToolCallChunk]] = None

class BaseBackend(ABC):
    """Abstract base class representing a unified LLM backend interface."""
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[BackendChunk, None]:
        """Requests a chat completion with streaming, yielding BackendChunks."""
        pass
