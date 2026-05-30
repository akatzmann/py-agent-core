import asyncio
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
from py_agent_core.backends.base import BaseBackend, BackendChunk, ToolCallChunk

class DummyBackend(BaseBackend):
    """Mock backend adapter that generates simulated streaming completions and tool calls offline."""
    
    def __init__(self, lorem_text: str = "Lorem ipsum dolor sit amet, consectetur adipiscing elit.", chunk_delay: float = 0.01):
        """
        Args:
            lorem_text: The simulated output text.
            chunk_delay: The time to sleep (in seconds) between streaming chunks.
        """
        self.lorem_text = lorem_text
        self.chunk_delay = chunk_delay

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[BackendChunk, None]:
        # Get the last user message content
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content") or ""
                break

        # Check if we already have tool results in the messages list since the user message.
        has_tool_response = False
        for msg in reversed(messages):
            if msg.get("role") == "user":
                break
            if msg.get("role") == "tool":
                has_tool_response = True
                break

        # Check if the user prompt explicitly requests a mock tool call
        # Format: "call_tool:tool_name:arguments_json"
        if tools and "call_tool:" in last_user_msg and not has_tool_response:
            parts = last_user_msg.split("call_tool:", 1)
            tool_spec = parts[1].strip()
            
            if ":" in tool_spec:
                tool_name, tool_args = tool_spec.split(":", 1)
                tool_name = tool_name.strip()
                tool_args = tool_args.strip()
                
                # Verify the tool is actually registered in options
                registered_names = [t["function"]["name"] for t in tools]
                if tool_name in registered_names:
                    # Emulate tool call chunks
                    yield BackendChunk(tool_calls=[
                        ToolCallChunk(index=0, id="mock_call_id", name=tool_name, arguments="")
                    ])
                    await asyncio.sleep(self.chunk_delay)
                    yield BackendChunk(tool_calls=[
                        ToolCallChunk(index=0, id="mock_call_id", arguments=tool_args)
                    ])
                    return

        # Default text generation
        words = self.lorem_text.split(" ")
        for idx, word in enumerate(words):
            suffix = " " if idx < len(words) - 1 else ""
            yield BackendChunk(text=word + suffix)
            await asyncio.sleep(self.chunk_delay)
