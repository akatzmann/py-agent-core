import sys
import uuid
from dataclasses import dataclass
from typing import Any, AsyncGenerator, List, Dict, Optional
from py_agent_core.backends.base import BaseBackend

@dataclass
class AgentEvent:
    """Event yielded by the PyAgent run loop."""
    type: str  # "text_delta", "tool_start", "tool_end", "interrupted", "done"
    content: Any = None

class PyAgent:
    """Core agent runtime class managing states, execution, and cooperative preemption."""
    
    def __init__(self, backend: BaseBackend, system_prompt: str, tools: Optional[List[Any]] = None):
        """
        Args:
            backend: A concrete BaseBackend implementation.
            system_prompt: System instructions for the agent.
            tools: List of tool functions decorated with @tool.
        """
        self.backend = backend
        self.system_prompt = system_prompt
        self.tools = {t.__name__: t for t in tools} if tools else {}
        self.history: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        self._interrupted = False

    def interrupt(self):
        """Signals the running agent loop to stop and terminate network streaming instantly."""
        self._interrupted = True

    async def run_loop(self, user_prompt: str) -> AsyncGenerator[AgentEvent, None]:
        """Runs the main execution loop asynchronously, yielding AgentEvents.
        
        Args:
            user_prompt: The user query or task.
        """
        self._interrupted = False
        self.history.append({"role": "user", "content": user_prompt})

        while True:
            # 1. Check for pre-execution interrupt
            if self._interrupted:
                yield AgentEvent("interrupted", "Execution halted before calling LLM.")
                return

            tool_definitions = [t.definition for t in self.tools.values()] if self.tools else None
            
            # Get completion generator from backend
            generator = self.backend.generate_stream(self.history, tools=tool_definitions)
            
            assistant_message = {"role": "assistant", "content": "", "tool_calls": []}
            accumulated_tool_calls = {}
            
            interrupted = False
            try:
                async for chunk in generator:
                    # 2. Check for mid-stream interrupt
                    if self._interrupted:
                        yield AgentEvent("interrupted", "Stream aborted mid-generation.")
                        interrupted = True
                        break

                    # Handle streaming text deltas
                    if chunk.text:
                        assistant_message["content"] += chunk.text
                        yield AgentEvent("text_delta", chunk.text)

                    # Handle streaming tool call deltas
                    if chunk.tool_calls:
                        for tc in chunk.tool_calls:
                            idx = tc.index
                            if idx not in accumulated_tool_calls:
                                tc_id = tc.id if tc.id else f"call_{idx}_{uuid.uuid4().hex[:8]}"
                                accumulated_tool_calls[idx] = {
                                    "id": tc_id,
                                    "name": tc.name,
                                    "arguments": tc.arguments or ""
                                }
                            else:
                                if tc.id:
                                    accumulated_tool_calls[idx]["id"] = tc.id
                                if tc.name:
                                    accumulated_tool_calls[idx]["name"] = tc.name
                                if tc.arguments:
                                    accumulated_tool_calls[idx]["arguments"] += tc.arguments
            except Exception as e:
                print(f"[PyAgent] Error during LLM completion stream: {e}", file=sys.stderr)
                yield AgentEvent("error", str(e))
                return
            
            if interrupted:
                await generator.aclose()
                return
            
            # Finalize message schema based on accumulated data
            if accumulated_tool_calls:
                formatted_tool_calls = []
                for idx in sorted(accumulated_tool_calls.keys()):
                    tc = accumulated_tool_calls[idx]
                    formatted_tool_calls.append({
                        "id": tc.get("id"),
                        "type": "function",
                        "function": {
                            "name": tc.get("name"),
                            "arguments": tc.get("arguments")
                        }
                    })
                assistant_message["tool_calls"] = formatted_tool_calls
                
            self.history.append(assistant_message)

            # 3. Handle Tool Execution Phase
            if assistant_message.get("tool_calls"):
                for tc in assistant_message["tool_calls"]:
                    # Check for interrupt before each tool execution
                    if self._interrupted:
                        yield AgentEvent("interrupted", "Execution aborted before running tool.")
                        return

                    tool_name = tc["function"]["name"]
                    tool_args = tc["function"]["arguments"]
                    tool_id = tc["id"]

                    if tool_name not in self.tools:
                        result = f"Error: Tool '{tool_name}' is not registered."
                    else:
                        yield AgentEvent("tool_start", tool_name)
                        try:
                            result = await self.tools[tool_name](tool_args)
                        except Exception as e:
                            result = f"Error executing tool: {str(e)}"
                        yield AgentEvent("tool_end", {"tool": tool_name, "result": result})

                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "content": str(result)
                    })
                # Re-loop to feed tool outputs back to LLM
                continue
            
            # No tool calls made, generation complete
            break

        yield AgentEvent("done", assistant_message["content"])
