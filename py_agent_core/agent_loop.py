import asyncio
import inspect
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional, Callable, Union, AsyncGenerator
from py_agent_core.backends.base import BaseBackend

# --- Event Types ---

@dataclass
class AgentStartEvent:
    type: str = "agent_start"

@dataclass
class AgentEndEvent:
    messages: List[Dict[str, Any]] = field(default_factory=list)
    type: str = "agent_end"

@dataclass
class TurnStartEvent:
    type: str = "turn_start"

@dataclass
class TurnEndEvent:
    message: Dict[str, Any] = field(default_factory=dict)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    type: str = "turn_end"

@dataclass
class MessageStartEvent:
    message: Dict[str, Any] = field(default_factory=dict)
    type: str = "message_start"

@dataclass
class MessageUpdateEvent:
    message: Dict[str, Any] = field(default_factory=dict)
    assistant_message_event: Dict[str, Any] = field(default_factory=dict)
    type: str = "message_update"

@dataclass
class MessageEndEvent:
    message: Dict[str, Any] = field(default_factory=dict)
    type: str = "message_end"

@dataclass
class ToolExecutionStartEvent:
    tool_call_id: str = ""
    tool_name: str = ""
    args: Any = None
    type: str = "tool_execution_start"

@dataclass
class ToolExecutionUpdateEvent:
    tool_call_id: str = ""
    tool_name: str = ""
    args: Any = None
    partial_result: Any = None
    type: str = "tool_execution_update"

@dataclass
class ToolExecutionEndEvent:
    tool_call_id: str = ""
    tool_name: str = ""
    result: Any = None
    is_error: bool = False
    type: str = "tool_execution_end"

@dataclass
class InterruptedEvent:
    reason: str = ""
    type: str = "interrupted"

@dataclass
class ErrorEvent:
    error: str = ""
    type: str = "error"

AgentEvent = Union[
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
]

# --- Context and Config Structs ---

@dataclass
class AgentContext:
    system_prompt: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    tools: List[Any] = field(default_factory=list)

@dataclass
class AgentLoopTurnUpdate:
    context: Optional[AgentContext] = None
    model: Optional[str] = None
    thinking_level: Optional[str] = None

@dataclass
class AgentLoopConfig:
    model: Any
    convert_to_llm: Callable[[List[Dict[str, Any]]], Union[List[Dict[str, Any]], Any]]
    emit: Callable[[AgentEvent], Any]
    thinking_level: str = "off"
    transform_context: Optional[Callable[[List[Dict[str, Any]], Optional[Any]], Any]] = None
    get_api_key: Optional[Callable[[str], Optional[str]]] = None
    should_stop_after_turn: Optional[Callable[[Any], Any]] = None
    prepare_next_turn: Optional[Callable[[Any], Optional[AgentLoopTurnUpdate]]] = None
    get_steering_messages: Optional[Callable[[], Any]] = None
    get_follow_up_messages: Optional[Callable[[], Any]] = None
    has_queued_messages: Optional[Callable[[], bool]] = None
    tool_execution: str = "parallel"  # "parallel" or "sequential"
    before_tool_call: Optional[Callable[[Any, Optional[Any]], Any]] = None
    after_tool_call: Optional[Callable[[Any, Optional[Any]], Any]] = None

# --- Abort Signal Simulator ---

class AbortSignal:
    def __init__(self):
        self._aborted = False

    @property
    def aborted(self) -> bool:
        return self._aborted

    def abort(self):
        self._aborted = True

# --- Async Helper ---

async def call_maybe_async(func: Optional[Callable], *args, **kwargs) -> Any:
    if not func:
        return None
    res = func(*args, **kwargs)
    if inspect.iscoroutine(res) or asyncio.iscoroutine(res):
        return await res
    return res

# --- Tool Helpers ---

async def prepare_tool_call(
    current_context: AgentContext,
    assistant_message: Dict[str, Any],
    tool_call: Dict[str, Any],
    config: AgentLoopConfig,
    signal: Optional[AbortSignal],
) -> Dict[str, Any]:
    tool_name = tool_call["function"]["name"]
    tool_args = tool_call["function"]["arguments"]
    
    tool_func = None
    for t in current_context.tools:
        if getattr(t, "__name__", None) == tool_name:
            tool_func = t
            break
            
    if not tool_func:
        return {
            "kind": "immediate",
            "result": {"content": [{"type": "text", "text": f"Error: Tool '{tool_name}' not found"}], "details": {}},
            "is_error": True
        }
        
    try:
        parsed_args = tool_args
        if isinstance(parsed_args, str):
            try:
                parsed_args = json.loads(parsed_args)
            except Exception:
                pass
                
        if config.before_tool_call:
            before_res = await call_maybe_async(config.before_tool_call, {
                "assistant_message": assistant_message,
                "tool_call": tool_call,
                "args": parsed_args,
                "context": current_context
            }, signal)
            
            if signal and signal.aborted:
                return {
                    "kind": "immediate",
                    "result": {"content": [{"type": "text", "text": "Operation aborted"}], "details": {}},
                    "is_error": True
                }
                
            if before_res and before_res.get("block"):
                return {
                    "kind": "immediate",
                    "result": {"content": [{"type": "text", "text": before_res.get("reason", "Tool execution was blocked")}], "details": {}},
                    "is_error": True
                }
                
        return {
            "kind": "prepared",
            "tool_call": tool_call,
            "tool": tool_func,
            "args": parsed_args
        }
    except Exception as e:
        return {
            "kind": "immediate",
            "result": {"content": [{"type": "text", "text": str(e)}], "details": {}},
            "is_error": True
        }

async def execute_prepared_tool_call(
    prepared: Dict[str, Any],
    signal: Optional[AbortSignal],
    emit: Callable[[AgentEvent], Any],
) -> Dict[str, Any]:
    tool_func = prepared["tool"]
    args = prepared["args"]
    tool_call = prepared["tool_call"]
    tool_id = tool_call["id"]
    tool_name = tool_call["function"]["name"]
    
    try:
        # Check signature to pass callbacks if accepted
        func_to_inspect = tool_func.func if hasattr(tool_func, "func") else tool_func
        sig = inspect.signature(func_to_inspect)
        kwargs = {}
        if "signal" in sig.parameters:
            kwargs["signal"] = signal
            
        def on_update(partial_res):
            async def _emit_update():
                await call_maybe_async(emit, ToolExecutionUpdateEvent(
                    tool_call_id=tool_id,
                    tool_name=tool_name,
                    args=args,
                    partial_result=partial_res
                ))
            # Schedule execution of update in loop
            asyncio.create_task(_emit_update())
            
        if "on_update" in sig.parameters:
            kwargs["on_update"] = on_update
            
        # Check if the callable is async
        is_coro = inspect.iscoroutinefunction(tool_func) or (
            hasattr(tool_func, "__call__") and inspect.iscoroutinefunction(tool_func.__call__)
        )
            
        # Invoke actual function
        if isinstance(args, dict):
            has_kwargs_param = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            if has_kwargs_param:
                passed_args = args
            else:
                passed_args = {k: v for k, v in args.items() if k in sig.parameters}
            
            if is_coro:
                res = await tool_func(**passed_args, **kwargs)
            else:
                res = await asyncio.to_thread(tool_func, **passed_args, **kwargs)
        else:
            if is_coro:
                res = await tool_func(args, **kwargs)
            else:
                res = await asyncio.to_thread(tool_func, args, **kwargs)
                
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
            
        return {"result": normalized_res, "is_error": False}
    except Exception as e:
        return {
            "result": {"content": [{"type": "text", "text": f"Error executing tool: {str(e)}"}], "details": {}},
            "is_error": True
        }

async def finalize_executed_tool_call(
    current_context: AgentContext,
    assistant_message: Dict[str, Any],
    prepared: Dict[str, Any],
    executed: Dict[str, Any],
    config: AgentLoopConfig,
    signal: Optional[AbortSignal],
) -> Dict[str, Any]:
    result = executed["result"]
    is_error = executed["is_error"]
    
    if config.after_tool_call:
        try:
            after_res = await call_maybe_async(config.after_tool_call, {
                "assistant_message": assistant_message,
                "tool_call": prepared["tool_call"],
                "args": prepared["args"],
                "result": result,
                "is_error": is_error,
                "context": current_context
            }, signal)
            
            if after_res:
                result = {
                    "content": after_res.get("content", result["content"]),
                    "details": after_res.get("details", result["details"]),
                    "terminate": after_res.get("terminate", result.get("terminate", False))
                }
                is_error = after_res.get("is_error", is_error)
        except Exception as e:
            result = {"content": [{"type": "text", "text": str(e)}], "details": {}}
            is_error = True
            
    return {
        "tool_call": prepared["tool_call"],
        "result": result,
        "is_error": is_error
    }

async def execute_tool_calls_sequential(
    current_context: AgentContext,
    assistant_message: Dict[str, Any],
    tool_calls: List[Dict[str, Any]],
    config: AgentLoopConfig,
    signal: Optional[AbortSignal],
) -> Dict[str, Any]:
    finalized_calls = []
    messages = []
    
    for tool_call in tool_calls:
        tool_id = tool_call["id"]
        tool_name = tool_call["function"]["name"]
        tool_args = tool_call["function"]["arguments"]
        
        await call_maybe_async(config.emit, ToolExecutionStartEvent(
            tool_call_id=tool_id,
            tool_name=tool_name,
            args=tool_args
        ))
        
        preparation = await prepare_tool_call(current_context, assistant_message, tool_call, config, signal)
        
        if preparation["kind"] == "immediate":
            finalized = {
                "tool_call": tool_call,
                "result": preparation["result"],
                "is_error": preparation["is_error"]
            }
        else:
            executed = await execute_prepared_tool_call(preparation, signal, config.emit)
            finalized = await finalize_executed_tool_call(
                current_context,
                assistant_message,
                preparation,
                executed,
                config,
                signal
            )
            
        await call_maybe_async(config.emit, ToolExecutionEndEvent(
            tool_call_id=tool_id,
            tool_name=tool_name,
            result=finalized["result"],
            is_error=finalized["is_error"]
        ))
        
        tr_msg = {
            "role": "toolResult",
            "tool_call_id": tool_id,
            "name": tool_name,
            "content": finalized["result"]["content"],
            "details": finalized["result"]["details"],
            "is_error": finalized["is_error"],
            "timestamp": int(time.time() * 1000)
        }
        await call_maybe_async(config.emit, MessageStartEvent(tr_msg))
        await call_maybe_async(config.emit, MessageEndEvent(tr_msg))
        
        finalized_calls.append(finalized)
        messages.append(tr_msg)
        
        if signal and signal.aborted:
            break
            
    terminate = len(finalized_calls) > 0 and all(c["result"].get("terminate") for c in finalized_calls)
    return {"messages": messages, "terminate": terminate}

async def execute_tool_calls_parallel(
    current_context: AgentContext,
    assistant_message: Dict[str, Any],
    tool_calls: List[Dict[str, Any]],
    config: AgentLoopConfig,
    signal: Optional[AbortSignal],
) -> Dict[str, Any]:
    finalized_calls_futures = []
    
    for tool_call in tool_calls:
        tool_id = tool_call["id"]
        tool_name = tool_call["function"]["name"]
        tool_args = tool_call["function"]["arguments"]
        
        await call_maybe_async(config.emit, ToolExecutionStartEvent(
            tool_call_id=tool_id,
            tool_name=tool_name,
            args=tool_args
        ))
        
        preparation = await prepare_tool_call(current_context, assistant_message, tool_call, config, signal)
        
        if preparation["kind"] == "immediate":
            finalized = {
                "tool_call": tool_call,
                "result": preparation["result"],
                "is_error": preparation["is_error"]
            }
            async def _emit_immediate(f=finalized):
                await call_maybe_async(config.emit, ToolExecutionEndEvent(
                    tool_call_id=tool_id,
                    tool_name=tool_name,
                    result=f["result"],
                    is_error=f["is_error"]
                ))
                return f
            finalized_calls_futures.append(_emit_immediate())
        else:
            async def run_tool_task(prep=preparation, tid=tool_id, tname=tool_name):
                executed = await execute_prepared_tool_call(prep, signal, config.emit)
                finalized = await finalize_executed_tool_call(
                    current_context,
                    assistant_message,
                    prep,
                    executed,
                    config,
                    signal
                )
                await call_maybe_async(config.emit, ToolExecutionEndEvent(
                    tool_call_id=tid,
                    tool_name=tname,
                    result=finalized["result"],
                    is_error=finalized["is_error"]
                ))
                return finalized
            finalized_calls_futures.append(run_tool_task())
            
    ordered_finalized_calls = await asyncio.gather(*finalized_calls_futures)
    
    messages = []
    for finalized in ordered_finalized_calls:
        tool_call = finalized["tool_call"]
        tool_id = tool_call["id"]
        tool_name = tool_call["function"]["name"]
        
        tr_msg = {
            "role": "toolResult",
            "tool_call_id": tool_id,
            "name": tool_name,
            "content": finalized["result"]["content"],
            "details": finalized["result"]["details"],
            "is_error": finalized["is_error"],
            "timestamp": int(time.time() * 1000)
        }
        await call_maybe_async(config.emit, MessageStartEvent(tr_msg))
        await call_maybe_async(config.emit, MessageEndEvent(tr_msg))
        messages.append(tr_msg)
        
    terminate = len(ordered_finalized_calls) > 0 and all(c["result"].get("terminate") for c in ordered_finalized_calls)
    return {"messages": messages, "terminate": terminate}

async def execute_tool_calls(
    current_context: AgentContext,
    assistant_message: Dict[str, Any],
    config: AgentLoopConfig,
    signal: Optional[AbortSignal],
) -> Dict[str, Any]:
    tool_calls = assistant_message.get("tool_calls", [])
    if not tool_calls:
        return {"messages": [], "terminate": False}
        
    has_sequential = False
    for tc in tool_calls:
        name = tc["function"]["name"]
        for t in current_context.tools:
            if getattr(t, "__name__", None) == name:
                if getattr(t, "execution_mode", "parallel") == "sequential":
                    has_sequential = True
                    break
        if has_sequential:
            break
            
    if config.tool_execution == "sequential" or has_sequential:
        return await execute_tool_calls_sequential(current_context, assistant_message, tool_calls, config, signal)
    return await execute_tool_calls_parallel(current_context, assistant_message, tool_calls, config, signal)

# --- Functional Loops ---

async def run_loop(
    initial_context: AgentContext,
    new_messages: List[Dict[str, Any]],
    initial_config: AgentLoopConfig,
    signal: Optional[AbortSignal],
    emit: Callable[[AgentEvent], Any],
    backend: BaseBackend,
) -> None:
    current_context = initial_context
    config = initial_config
    first_turn = True
    
    pending_messages = []
    if config.get_steering_messages:
        pending_messages = await call_maybe_async(config.get_steering_messages)
            
    while True:
        has_more_tool_calls = True
        
        while has_more_tool_calls or pending_messages:
            if signal and signal.aborted:
                await call_maybe_async(emit, InterruptedEvent("Execution aborted."))
                return
                
            if not first_turn:
                await call_maybe_async(emit, TurnStartEvent())
            else:
                first_turn = False
                
            if pending_messages:
                for msg in pending_messages:
                    await call_maybe_async(emit, MessageStartEvent(msg))
                    await call_maybe_async(emit, MessageEndEvent(msg))
                    current_context.messages.append(msg)
                    new_messages.append(msg)
                pending_messages = []
                
            # Prepend system prompt if not present
            messages_to_convert = current_context.messages
            has_system = any(m.get("role") == "system" for m in messages_to_convert)
            if current_context.system_prompt and not has_system:
                messages_to_convert = [{"role": "system", "content": current_context.system_prompt}] + list(messages_to_convert)

            # Context transformation
            if config.transform_context:
                messages_to_convert = await call_maybe_async(config.transform_context, messages_to_convert, signal)
                    
            # Convert to LLM format
            llm_messages = await call_maybe_async(config.convert_to_llm, messages_to_convert)
                
            tool_definitions = [t.definition for t in current_context.tools] if current_context.tools else None
            
            # Request streaming LLM completion
            sig = inspect.signature(backend.generate_stream)
            if "options" in sig.parameters:
                generator = backend.generate_stream(
                    llm_messages,
                    tools=tool_definitions,
                    options={"thinking_level": config.thinking_level}
                )
            else:
                generator = backend.generate_stream(
                    llm_messages,
                    tools=tool_definitions
                )
            
            assistant_message = {"role": "assistant", "content": "", "thinking": "", "tool_calls": []}
            await call_maybe_async(emit, MessageStartEvent(assistant_message))
            
            accumulated_tool_calls = {}
            interrupted = False
            
            try:
                async for chunk in generator:
                    if signal and signal.aborted:
                        await call_maybe_async(emit, InterruptedEvent("Execution aborted during streaming."))
                        interrupted = True
                        break
                        
                    if getattr(chunk, "thinking", None):
                        assistant_message["thinking"] += chunk.thinking
                        await call_maybe_async(emit, MessageUpdateEvent(
                            message=assistant_message,
                            assistant_message_event={"type": "thinking_delta", "delta": chunk.thinking}
                        ))

                    if chunk.text:
                        assistant_message["content"] += chunk.text
                        await call_maybe_async(emit, MessageUpdateEvent(
                            message=assistant_message,
                            assistant_message_event={"type": "text_delta", "delta": chunk.text}
                        ))
                        
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
                                    
                            await call_maybe_async(emit, MessageUpdateEvent(
                                message=assistant_message,
                                assistant_message_event={"type": "toolcall_delta", "delta": tc.arguments, "index": idx}
                            ))
            except Exception as e:
                await call_maybe_async(emit, ErrorEvent(str(e)))
                raise
            finally:
                if hasattr(generator, "aclose"):
                    await generator.aclose()
                    
            if interrupted:
                return
                
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
                
            await call_maybe_async(emit, MessageEndEvent(assistant_message))
            current_context.messages.append(assistant_message)
            new_messages.append(assistant_message)
            
            # Execute tool calls
            tool_results = []
            has_more_tool_calls = False
            
            tool_calls = assistant_message.get("tool_calls", [])
            if tool_calls:
                execution_batch = await execute_tool_calls(current_context, assistant_message, config, signal)
                tool_results = execution_batch["messages"]
                has_more_tool_calls = not execution_batch["terminate"]
                
                for tr in tool_results:
                    current_context.messages.append(tr)
                    new_messages.append(tr)
                    
            await call_maybe_async(emit, TurnEndEvent(assistant_message, tool_results))
            
            # prepareNextTurn hook
            if config.prepare_next_turn:
                next_context = {
                    "message": assistant_message,
                    "tool_results": tool_results,
                    "context": current_context,
                    "new_messages": new_messages,
                }
                next_turn_update = await call_maybe_async(config.prepare_next_turn, next_context)
                    
                if next_turn_update:
                    if getattr(next_turn_update, "context", None):
                        current_context = next_turn_update.context
                    elif isinstance(next_turn_update, dict) and "context" in next_turn_update:
                        current_context = next_turn_update["context"]
                        
                    # Apply updated model/backend
                    next_model = getattr(next_turn_update, "model", None)
                    if not next_model and isinstance(next_turn_update, dict):
                        next_model = next_turn_update.get("model")
                    if next_model:
                        backend = next_model
                        
                    # Apply updated thinking level
                    next_thinking = getattr(next_turn_update, "thinking_level", None)
                    if not next_thinking and isinstance(next_turn_update, dict):
                        next_thinking = next_turn_update.get("thinking_level")
                    if next_thinking:
                        config.thinking_level = next_thinking
                        
            # shouldStopAfterTurn hook
            if config.should_stop_after_turn:
                should_stop = await call_maybe_async(config.should_stop_after_turn, {
                    "message": assistant_message,
                    "tool_results": tool_results,
                    "context": current_context,
                    "new_messages": new_messages,
                })
                    
                if should_stop:
                    await call_maybe_async(emit, AgentEndEvent(messages=new_messages))
                    return
                    
            if config.get_steering_messages:
                pending_messages = await call_maybe_async(config.get_steering_messages)
                    
        # Check follow-up messages
        follow_up = []
        if config.get_follow_up_messages:
            follow_up = await call_maybe_async(config.get_follow_up_messages)
                
        if follow_up:
            pending_messages = follow_up
            continue
            
        break
        
    await call_maybe_async(emit, AgentEndEvent(messages=new_messages))

async def agent_loop(
    prompts: List[Dict[str, Any]],
    context: AgentContext,
    config: AgentLoopConfig,
    backend: BaseBackend,
    signal: Optional[AbortSignal] = None,
) -> List[Dict[str, Any]]:
    new_messages = []
    current_context = AgentContext(
        system_prompt=context.system_prompt,
        messages=list(context.messages) + list(prompts),
        tools=list(context.tools) if context.tools else []
    )
    
    await call_maybe_async(config.emit, AgentStartEvent())
    await call_maybe_async(config.emit, TurnStartEvent())
    for p in prompts:
        await call_maybe_async(config.emit, MessageStartEvent(p))
        await call_maybe_async(config.emit, MessageEndEvent(p))
        new_messages.append(p)
        
    await run_loop(current_context, new_messages, config, signal, config.emit, backend)
    return new_messages

async def agent_loop_continue(
    context: AgentContext,
    config: AgentLoopConfig,
    backend: BaseBackend,
    signal: Optional[AbortSignal] = None,
) -> List[Dict[str, Any]]:
    if not context.messages:
        raise ValueError("Cannot continue: no messages in context")
    if context.messages[-1].get("role") == "assistant":
        has_queued = False
        if config.has_queued_messages:
            has_queued = config.has_queued_messages()
        if not has_queued:
            raise ValueError("Cannot continue from message role: assistant")
        
    new_messages = []
    current_context = AgentContext(
        system_prompt=context.system_prompt,
        messages=list(context.messages),
        tools=list(context.tools) if context.tools else []
    )
    
    await call_maybe_async(config.emit, AgentStartEvent())
    await call_maybe_async(config.emit, TurnStartEvent())
    
    await run_loop(current_context, new_messages, config, signal, config.emit, backend)
    return new_messages
