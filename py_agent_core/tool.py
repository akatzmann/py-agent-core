import asyncio
import inspect
import re
import json
from typing import Callable, Any, Dict, Optional, Tuple, get_type_hints
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
    def __init__(self, func: Callable):
        self.func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        
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
        
        if inspect.iscoroutinefunction(self.func):
            return await self.func(*args, **kwargs)
        else:
            # Run in executor if it's synchronous to prevent blocking the async loop
            return await asyncio.to_thread(self.func, *args, **kwargs)

def tool(func: Callable) -> Tool:
    """Decorator to convert a standard Python function into an LLM-compatible tool.
    
    Parses function name, parameters, type hints, and docstrings automatically.
    """
    return Tool(func)
