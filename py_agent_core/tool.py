import asyncio
import inspect
import re
import json
import time
from typing import Callable, Any, Dict, Optional, Tuple, get_type_hints, Union
from functools import wraps

def parse_docstring(doc: Optional[str]) -> Tuple[str, Dict[str, str]]:
    if not doc:
        return "", {}
    
    lines = doc.splitlines()
    description_lines = []
    param_descriptions = {}
    
    in_args_section = False
    current_param = None
    
    arg_headers = {"args", "arguments", "parameters", "params"}
    
    for line in lines:
        stripped = line.strip()
        
        # Check if we are entering an arguments block
        if stripped.lower().rstrip(":") in arg_headers:
            in_args_section = True
            continue
        
        if in_args_section:
            # Check for Google/Numpy style parameter declaration: 'name: description' or 'name (type): description'
            google_match = re.match(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(\([^\)]+\))?\s*:\s*(.*)$", line)
            if google_match:
                current_param = google_match.group(1)
                desc = google_match.group(3).strip()
                param_descriptions[current_param] = desc
                continue
            
            # Sphinx style: ':param name: description'
            sphinx_match = re.match(r"^:param\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$", stripped)
            if sphinx_match:
                current_param = sphinx_match.group(1)
                desc = sphinx_match.group(2).strip()
                param_descriptions[current_param] = desc
                continue
            
            # If line is indented, it's a continuation of the current parameter's description
            if current_param and (line.startswith(" ") or line.startswith("\t")) and stripped:
                param_descriptions[current_param] += " " + stripped
                continue
            
            # If line is not empty and is not indented, we exited the args section
            if stripped != "" and not line.startswith(" ") and not line.startswith("\t"):
                in_args_section = False
                current_param = None
        
        if not in_args_section:
            # Sphinx style match can appear anywhere
            sphinx_match = re.match(r"^:param\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$", stripped)
            if sphinx_match:
                current_param = sphinx_match.group(1)
                desc = sphinx_match.group(2).strip()
                param_descriptions[current_param] = desc
                continue
            
            description_lines.append(line)
            
    main_desc = "\n".join(description_lines).strip()
    return main_desc, param_descriptions

def map_type(py_type) -> str:
    if py_type is str:
        return "string"
    elif py_type is int:
        return "integer"
    elif py_type is float:
        return "number"
    elif py_type is bool:
        return "boolean"
    elif py_type is dict:
        return "object"
    elif py_type is list:
        return "array"
    return "string"

class Tool:
    def __init__(self, func: Callable, execution_mode: str = "parallel"):
        self.func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.execution_mode = getattr(func, "execution_mode", execution_mode)
        
        # Extrospect metadata
        self.definition = self._build_definition()
        wraps(func)(self)

    def _build_definition(self) -> Dict[str, Any]:
        # Parse signature
        sig = inspect.signature(self.func)
        type_hints = get_type_hints(self.func)
        doc_desc, param_descs = parse_docstring(self.__doc__)
        
        properties = {}
        required = []
        
        for name, param in sig.parameters.items():
            if name == "self" or name == "cls":
                continue
            
            py_type = type_hints.get(name, str)
            json_type = map_type(py_type)
            
            param_def = {"type": json_type}
            
            # Add description if parsed from docstring
            if name in param_descs:
                param_def["description"] = param_descs[name]
                
            # Add default value if defined
            if param.default is not inspect.Parameter.empty:
                param_def["default"] = param.default
            else:
                required.append(name)
                
            properties[name] = param_def
            
        return {
            "type": "function",
            "function": {
                "name": self.__name__,
                "description": doc_desc,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
        }

    async def __call__(self, *args, **kwargs) -> Any:
        # If arguments are passed as a single string/dict (common in LLM tool calling triggers),
        # parse them appropriately.
        if len(args) == 1 and isinstance(args[0], str) and not kwargs:
            try:
                parsed_args = json.loads(args[0])
                if isinstance(parsed_args, dict):
                    kwargs = parsed_args
                    args = ()
            except json.JSONDecodeError:
                pass
        
        if self.execution_mode == "background":
            from py_agent_core.agent import _active_agent_ctx
            agent = _active_agent_ctx.get()
            if not agent:
                raise RuntimeError("No active agent context found for background tool execution.")
                
            tool_name = self.__name__
            
            # Find tool call ID from history
            tool_call_id = None
            last_msg = agent.state.messages[-1] if agent.state.messages else {}
            if last_msg.get("role") == "assistant" and "tool_calls" in last_msg:
                for tc in last_msg["tool_calls"]:
                    if tc["function"]["name"] == tool_name:
                        tool_call_id = tc["id"]
                        break
            
            if not tool_call_id:
                import uuid
                tool_call_id = f"bg_{tool_name}_{uuid.uuid4().hex[:8]}"
                
            async def run_in_background():
                try:
                    if inspect.iscoroutinefunction(self.func):
                        res = await self.func(*args, **kwargs)
                    else:
                        res = await asyncio.to_thread(self.func, *args, **kwargs)
                except Exception as e:
                    res = f"Error in background tool: {str(e)}"
                
                # Normalize response
                normalized_res = {"content": "", "details": {}, "terminate": False}
                if isinstance(res, dict):
                    normalized_res["content"] = res.get("content", str(res))
                    normalized_res["details"] = res.get("details", res)
                    normalized_res["terminate"] = res.get("terminate", False)
                elif hasattr(res, "content"):
                    normalized_res["content"] = getattr(res, "content")
                    normalized_res["details"] = getattr(res, "details", {})
                    normalized_res["terminate"] = getattr(res, "terminate", False)
                else:
                    normalized_res["content"] = str(res)
                    normalized_res["details"] = {"result": res}
                    
                if isinstance(normalized_res["content"], str):
                    normalized_res["content"] = [{"type": "text", "text": normalized_res["content"]}]
                    
                payload = {
                    "role": "toolResult",
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": normalized_res["content"],
                    "details": normalized_res["details"],
                    "is_error": False,
                    "timestamp": int(time.time() * 1000)
                }
                
                # Steer or follow-up
                if agent.active_run:
                    # If the agent is currently running, queue the result as a steering message.
                    # The active loop will naturally pick it up at the end of the current turn without interruption.
                    agent.steer(payload)
                else:
                    # If the agent is idle, queue the result as a follow-up and trigger continuation
                    agent.follow_up(payload)
                    asyncio.create_task(agent.continue_())
                
            # Schedule execution of the actual tool in background
            asyncio.create_task(run_in_background())
            return f"Task '{tool_name}' started in background."
            
        if inspect.iscoroutinefunction(self.func):
            return await self.func(*args, **kwargs)
        else:
            # Run in executor if it's synchronous to prevent blocking the async loop
            return await asyncio.to_thread(self.func, *args, **kwargs)

def tool(func: Optional[Callable] = None, *, execution_mode: str = "parallel") -> Union[Tool, Callable[[Callable], Tool]]:
    """Decorator to convert a standard Python function into an LLM-compatible tool.
    
    Parses function name, parameters, type hints, and docstrings automatically.
    """
    if func is None:
        def decorator(f: Callable) -> Tool:
            return Tool(f, execution_mode=execution_mode)
        return decorator
    return Tool(func, execution_mode=execution_mode)
