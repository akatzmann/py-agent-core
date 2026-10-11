from typing import List, Dict, Any, Optional, Tuple
from py_agent_core.backends.base import BackendChunk, ToolCallChunk


def _convert_messages_for_responses(
    messages: List[Dict[str, Any]],
) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """
    Converts standard chat completion message history into (instructions, input_items)
    for the OpenAI /v1/responses API.
    """
    instructions_parts: List[str] = []
    input_items: List[Dict[str, Any]] = []

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")

        if role in ("system", "developer"):
            if content:
                instructions_parts.append(content)
            continue

        if role == "user":
            input_items.append({
                "type": "message",
                "role": "user",
                "content": content or "",
            })
        elif role == "assistant":
            # If assistant produced text content, add message item
            if content:
                input_items.append({
                    "type": "message",
                    "role": "assistant",
                    "content": content,
                })
            # If assistant produced tool calls, add function_call items
            tool_calls = msg.get("tool_calls") or []
            for tc in tool_calls:
                call_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                func = tc.get("function") if isinstance(tc, dict) else getattr(tc, "function", None)
                name = func.get("name") if isinstance(func, dict) else getattr(func, "name", "")
                arguments = func.get("arguments") if isinstance(func, dict) else getattr(func, "arguments", "")
                input_items.append({
                    "type": "function_call",
                    "call_id": call_id or "",
                    "name": name or "",
                    "arguments": arguments or "",
                })
        elif role == "tool":
            call_id = msg.get("tool_call_id") or msg.get("id") or ""
            input_items.append({
                "type": "function_call_output",
                "call_id": call_id,
                "output": str(content) if content is not None else "",
            })

    instructions = "\n\n".join(instructions_parts) if instructions_parts else None
    return instructions, input_items


def _convert_tools_for_responses(
    tools: Optional[List[Dict[str, Any]]],
) -> Optional[List[Dict[str, Any]]]:
    """
    Converts standard OpenAI chat tool definitions to /v1/responses tool definitions.
    Flattens {"type": "function", "function": {...}} into {"type": "function", "name": ..., ...}.
    """
    if not tools:
        return None

    converted = []
    for tool in tools:
        if isinstance(tool, dict) and "function" in tool and isinstance(tool["function"], dict):
            fn = tool["function"]
            t: Dict[str, Any] = {
                "type": "function",
                "name": fn.get("name"),
            }
            if "description" in fn:
                t["description"] = fn["description"]
            if "parameters" in fn:
                t["parameters"] = fn["parameters"]
            if "strict" in fn:
                t["strict"] = fn["strict"]
            converted.append(t)
        elif isinstance(tool, dict):
            converted.append(dict(tool))
        else:
            converted.append(tool)

    return converted


class ResponsesStreamTracker:
    """
    Tracks streaming items and deltas from /v1/responses and translates them
    into py-agent-core BackendChunk objects.
    """

    def __init__(self):
        self._output_index_to_tool_index: Dict[int, int] = {}
        self._item_id_to_tool_index: Dict[str, int] = {}
        self._tool_calls: Dict[int, Dict[str, Any]] = {}
        self._next_tool_index: int = 0

    def _get_or_create_tool_index(self, output_index: Optional[int], item_id: Optional[str]) -> int:
        if output_index is not None and output_index in self._output_index_to_tool_index:
            return self._output_index_to_tool_index[output_index]
        if item_id is not None and item_id in self._item_id_to_tool_index:
            return self._item_id_to_tool_index[item_id]

        idx = self._next_tool_index
        self._next_tool_index += 1
        if output_index is not None:
            self._output_index_to_tool_index[output_index] = idx
        if item_id is not None:
            self._item_id_to_tool_index[item_id] = idx
        return idx

    def handle_event(self, event: Any) -> List[BackendChunk]:
        event_type = getattr(event, "type", None)
        if event_type is None and isinstance(event, dict):
            event_type = event.get("type")

        if not event_type:
            return []

        # 1. Output text deltas
        if event_type in ("response.output_text.delta", "response.text.delta"):
            delta = getattr(event, "delta", None)
            if delta is None and isinstance(event, dict):
                delta = event.get("delta")
            if delta:
                return [BackendChunk(text=delta)]
            return []

        # 2. Reasoning text deltas
        if event_type in ("response.reasoning_text.delta", "response.reasoning.text.delta"):
            delta = getattr(event, "delta", None)
            if delta is None and isinstance(event, dict):
                delta = event.get("delta")
            if delta:
                return [BackendChunk(thinking=delta)]
            return []

        # 3. Output item added (initial function call)
        if event_type == "response.output_item.added":
            item = getattr(event, "item", None)
            if item is None and isinstance(event, dict):
                item = event.get("item")
            item_type = getattr(item, "type", None)
            if item_type is None and isinstance(item, dict):
                item_type = item.get("type")

            if item_type == "function_call":
                output_index = getattr(event, "output_index", None)
                if output_index is None and isinstance(event, dict):
                    output_index = event.get("output_index")
                call_id = getattr(item, "call_id", None) or getattr(item, "id", None)
                if call_id is None and isinstance(item, dict):
                    call_id = item.get("call_id") or item.get("id")
                name = getattr(item, "name", None)
                if name is None and isinstance(item, dict):
                    name = item.get("name")
                arguments = getattr(item, "arguments", "") or ""
                if not arguments and isinstance(item, dict):
                    arguments = item.get("arguments", "")

                tool_idx = self._get_or_create_tool_index(output_index, call_id)
                self._tool_calls[tool_idx] = {
                    "id": call_id,
                    "name": name,
                    "arguments": arguments,
                }
                return [BackendChunk(tool_calls=[ToolCallChunk(
                    index=tool_idx,
                    id=call_id,
                    name=name,
                    arguments=arguments
                )])]
            return []

        # 4. Function call arguments delta
        if event_type == "response.function_call_arguments.delta":
            output_index = getattr(event, "output_index", None)
            if output_index is None and isinstance(event, dict):
                output_index = event.get("output_index")
            item_id = getattr(event, "item_id", None)
            if item_id is None and isinstance(event, dict):
                item_id = event.get("item_id")
            delta = getattr(event, "delta", "") or ""
            if not delta and isinstance(event, dict):
                delta = event.get("delta", "")

            tool_idx = self._get_or_create_tool_index(output_index, item_id)
            call_info = self._tool_calls.get(tool_idx, {})
            call_id = call_info.get("id") or item_id
            return [BackendChunk(tool_calls=[ToolCallChunk(
                index=tool_idx,
                id=call_id,
                name=None,
                arguments=delta
            )])]

        # 5. Output item done (fallback when arguments weren't streamed as deltas)
        if event_type == "response.output_item.done":
            item = getattr(event, "item", None)
            if item is None and isinstance(event, dict):
                item = event.get("item")
            item_type = getattr(item, "type", None)
            if item_type is None and isinstance(item, dict):
                item_type = item.get("type")

            if item_type == "function_call":
                output_index = getattr(event, "output_index", None)
                if output_index is None and isinstance(event, dict):
                    output_index = event.get("output_index")
                call_id = getattr(item, "call_id", None) or getattr(item, "id", None)
                if call_id is None and isinstance(item, dict):
                    call_id = item.get("call_id") or item.get("id")
                name = getattr(item, "name", None)
                if name is None and isinstance(item, dict):
                    name = item.get("name")
                arguments = getattr(item, "arguments", "") or ""
                if not arguments and isinstance(item, dict):
                    arguments = item.get("arguments", "")

                tool_idx = self._get_or_create_tool_index(output_index, call_id)
                if tool_idx not in self._tool_calls:
                    self._tool_calls[tool_idx] = {
                        "id": call_id,
                        "name": name,
                        "arguments": arguments,
                    }
                    return [BackendChunk(tool_calls=[ToolCallChunk(
                        index=tool_idx,
                        id=call_id,
                        name=name,
                        arguments=arguments
                    )])]
            return []

        return []
