import asyncio
import contextvars
import inspect
import time
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional, Set, Callable, Union, AsyncGenerator
from py_agent_core.backends.base import BaseBackend

# Context variable to track the active agent instance executing tools in the current task/thread
_active_agent_ctx = contextvars.ContextVar("active_agent", default=None)
from py_agent_core.agent_loop import (
    agent_loop,
    agent_loop_continue,
    AgentContext,
    AgentLoopConfig,
    AgentLoopTurnUpdate,
    AbortSignal,
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

# --- Legacy Event Compatibility ---

@dataclass
class LegacyAgentEvent:
    """Legacy Event returned by PyAgent.run_loop for backward compatibility."""
    type: str  # "text_delta", "tool_start", "tool_end", "interrupted", "done", "error"
    content: Any = None

# For backward compatibility
AgentEventCompat = LegacyAgentEvent

# --- Queues ---

class PendingMessageQueue:
    def __init__(self, mode: str = "one-at-a-time"):
        self.messages = []
        self.mode = mode

    def enqueue(self, message: Dict[str, Any]):
        self.messages.append(message)

    def has_items(self) -> bool:
        return len(self.messages) > 0

    def drain(self) -> List[Dict[str, Any]]:
        if self.mode == "all":
            drained = list(self.messages)
            self.messages = []
            return drained
        else:
            if not self.messages:
                return []
            first = self.messages[0]
            self.messages = self.messages[1:]
            return [first]

    def clear(self):
        self.messages = []

# --- Public State ---

class AgentState:
    """Public state of the Agent orchestrator."""
    def __init__(
        self,
        system_prompt: str = "",
        model: Any = None,
        thinking_level: str = "off",
        tools: Optional[List[Any]] = None,
        messages: Optional[List[Dict[str, Any]]] = None
    ):
        self.system_prompt = system_prompt
        self.model = model
        self.thinking_level = thinking_level
        self._tools = list(tools) if tools else []
        self._messages = list(messages) if messages else []
        self.is_streaming = False
        self.streaming_message: Optional[Dict[str, Any]] = None
        self.pending_tool_calls: Set[str] = set()
        self.error_message: Optional[str] = None

    @property
    def tools(self) -> List[Any]:
        return self._tools

    @tools.setter
    def tools(self, next_tools: List[Any]):
        self._tools = list(next_tools)

    @property
    def messages(self) -> List[Dict[str, Any]]:
        return self._messages

    @messages.setter
    def messages(self, next_messages: List[Dict[str, Any]]):
        self._messages = list(next_messages)

# --- Active Run Orchestrator ---

class ActiveRun:
    def __init__(self, task: asyncio.Task, abort_signal: AbortSignal):
        self.task = task
        self.abort_signal = abort_signal

# --- Default Translator ---

def default_convert_to_llm(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    llm_msgs = []
    for msg in messages:
        role = msg.get("role")
        if role in ("user", "assistant", "system", "tool"):
            llm_msgs.append(msg)
        elif role == "toolResult":
            # Map toolResult to standard tool role for LLM
            llm_msgs.append({
                "role": "tool",
                "tool_call_id": msg.get("tool_call_id"),
                "name": msg.get("name"),
                "content": str(msg.get("content"))
            })
    return llm_msgs

# --- Stateful Agent Class ---

class Agent:
    """Stateful wrapper class orchestrating the agent execution loop, transcript state, and hooks."""
    
    def __init__(
        self,
        backend: BaseBackend,
        initial_state: Optional[Dict[str, Any]] = None,
        convert_to_llm: Optional[Callable[[List[Dict[str, Any]]], Any]] = None,
        transform_context: Optional[Callable[[List[Dict[str, Any]], Optional[AbortSignal]], Any]] = None,
        before_tool_call: Optional[Callable[[Any, Optional[AbortSignal]], Any]] = None,
        after_tool_call: Optional[Callable[[Any, Optional[AbortSignal]], Any]] = None,
        prepare_next_turn: Optional[Callable[[Any], Any]] = None,
        should_stop_after_turn: Optional[Callable[[Any], Any]] = None,
        tool_execution: str = "parallel",
        steering_mode: str = "one-at-a-time",
        follow_up_mode: str = "one-at-a-time",
    ):
        self.backend = backend
        
        # Initialize state
        state_dict = initial_state or {}
        self._state = AgentState(
            system_prompt=state_dict.get("systemPrompt", ""),
            model=state_dict.get("model", backend),
            thinking_level=state_dict.get("thinkingLevel", "off"),
            tools=state_dict.get("tools", []),
            messages=state_dict.get("messages", [])
        )
        
        self.listeners = set()
        self.convertToLlm = convert_to_llm or default_convert_to_llm
        self.transformContext = transform_context
        self.beforeToolCall = before_tool_call
        self.afterToolCall = after_tool_call
        self.prepareNextTurn = prepare_next_turn
        self.shouldStopAfterTurn = should_stop_after_turn
        
        self.steering_queue = PendingMessageQueue(steering_mode)
        self.follow_up_queue = PendingMessageQueue(follow_up_mode)
        self.tool_execution = tool_execution
        
        self.active_run: Optional[ActiveRun] = None

    @property
    def state(self) -> AgentState:
        return self._state

    @property
    def steering_mode(self) -> str:
        return self.steering_queue.mode

    @steering_mode.setter
    def steering_mode(self, mode: str):
        self.steering_queue.mode = mode

    @property
    def follow_up_mode(self) -> str:
        return self.follow_up_queue.mode

    @follow_up_mode.setter
    def follow_up_mode(self, mode: str):
        self.follow_up_queue.mode = mode

    def subscribe(self, listener: Callable[[AgentEvent, AbortSignal], Any]) -> Callable[[], None]:
        """Subscribe to loop events. Returns unsubscribe callable."""
        self.listeners.add(listener)
        return lambda: self.listeners.discard(listener)

    def steer(self, message: Dict[str, Any]):
        """Inject user message mid-run after active tools finish."""
        self.steering_queue.enqueue(message)

    def follow_up(self, message: Dict[str, Any]):
        """Inject message to run after current turn/idle."""
        self.follow_up_queue.enqueue(message)

    def clear_steering_queue(self):
        self.steering_queue.clear()

    def clear_follow_up_queue(self):
        self.follow_up_queue.clear()

    def clear_all_queues(self):
        self.clear_steering_queue()
        self.clear_follow_up_queue()

    def has_queued_messages(self) -> bool:
        return self.steering_queue.has_items() or self.follow_up_queue.has_items()

    def abort(self):
        """Abort active loop execution instantly."""
        if self.active_run:
            self.active_run.abort_signal.abort()

    async def wait_for_idle(self):
        """Wait until active loop execution settled."""
        if self.active_run:
            try:
                await self.active_run.task
            except asyncio.CancelledError:
                pass

    def reset(self):
        """Reset messages, active state, queues."""
        self._state.messages = []
        self._state.is_streaming = False
        self._state.streaming_message = None
        self._state.pending_tool_calls = set()
        self._state.error_message = None
        self.clear_all_queues()

    # --- Prompt / Invocation interfaces ---

    async def prompt(self, content: Union[str, Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """Run execution turn for prompt(s) in awaitable mode."""
        if self.active_run:
            raise RuntimeError("Agent is already running. Use steer() or follow_up() to queue messages.")
            
        prompts = self._normalize_input(content)
        await self._run_lifecycle(lambda signal: agent_loop(
            prompts=prompts,
            context=self._create_context_snapshot(),
            config=self._create_loop_config(),
            backend=self.backend,
            signal=signal
        ))

    async def continue_(self) -> None:
        """Resume execution loop from current context state."""
        if self.active_run:
            raise RuntimeError("Agent is already running.")
            
        await self._run_lifecycle(lambda signal: agent_loop_continue(
            context=self._create_context_snapshot(),
            config=self._create_loop_config(),
            backend=self.backend,
            signal=signal
        ))

    async def prompt_stream(
        self,
        content: Union[str, Dict[str, Any], List[Dict[str, Any]]]
    ) -> AsyncGenerator[AgentEvent, None]:
        """Stream granular loop events directly as an async generator."""
        if self.active_run:
            raise RuntimeError("Agent is already running.")
            
        prompts = self._normalize_input(content)
        abort_signal = AbortSignal()
        
        # State setup
        self._state.is_streaming = True
        self._state.streaming_message = None
        self._state.error_message = None
        
        # Run functional generator in loop
        loop_config = self._create_loop_config(custom_emit=None)
        
        queue = asyncio.Queue()
        async def event_sink(event: AgentEvent):
            await queue.put(event)
            
        loop_config.emit = event_sink
        
        async def run_task():
            token = _active_agent_ctx.set(self)
            try:
                await agent_loop(
                    prompts=prompts,
                    context=self._create_context_snapshot(),
                    config=loop_config,
                    backend=self.backend,
                    signal=abort_signal
                )
            except Exception as e:
                import traceback
                traceback.print_exc()
                await queue.put(ErrorEvent(str(e)))
            finally:
                _active_agent_ctx.reset(token)
                await queue.put(None)
                
        task = asyncio.create_task(run_task())
        self.active_run = ActiveRun(task=task, abort_signal=abort_signal)
        
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                    
                # Feed state reductions and notify subscribers
                await self._process_events(event)
                yield event
        finally:
            self._finish_run()

    # --- Internal Lifecycle Drivers ---

    def _normalize_input(self, content: Any) -> List[Dict[str, Any]]:
        if isinstance(content, list):
            return content
        if isinstance(content, dict):
            return [content]
        return [{
            "role": "user",
            "content": str(content),
            "timestamp": int(time.time() * 1000)
        }]

    def _create_context_snapshot(self) -> AgentContext:
        return AgentContext(
            system_prompt=self._state.system_prompt,
            messages=list(self._state.messages),
            tools=list(self._state.tools)
        )

    def _create_loop_config(self, custom_emit: Optional[Callable] = None) -> AgentLoopConfig:
        emit_func = custom_emit or (lambda e: self._process_events(e))
        return AgentLoopConfig(
            model=self._state.model,
            convert_to_llm=self.convertToLlm,
            emit=emit_func,
            transform_context=self.transformContext,
            get_api_key=self.get_api_key,
            should_stop_after_turn=self.shouldStopAfterTurn,
            prepare_next_turn=self.prepareNextTurn,
            get_steering_messages=lambda: self.steering_queue.drain(),
            get_follow_up_messages=lambda: self.follow_up_queue.drain(),
            has_queued_messages=lambda: self.has_queued_messages(),
            tool_execution=self.tool_execution,
            before_tool_call=self.beforeToolCall,
            after_tool_call=self.afterToolCall
        )

    async def get_api_key(self, provider: str) -> Optional[str]:
        # Proxy or dummy resolution
        return None

    async def _process_events(self, event: AgentEvent) -> None:
        abort_signal = self.active_run.abort_signal if self.active_run else None
        await self._process_state_reductions(event, abort_signal)
        
        # Notify subscribers
        for listener in list(self.listeners):
            res = listener(event, abort_signal)
            if inspect.iscoroutine(res):
                await res

    async def _process_state_reductions(self, event: AgentEvent, signal: Optional[AbortSignal]) -> None:
        if event.type == "message_start":
            self._state.streaming_message = getattr(event, "message", None)
        elif event.type == "message_update":
            self._state.streaming_message = getattr(event, "message", None)
        elif event.type == "message_end":
            self._state.streaming_message = None
            msg = getattr(event, "message", None)
            if msg:
                self._state.messages.append(msg)
        elif event.type == "tool_execution_start":
            self._state.pending_tool_calls.add(getattr(event, "tool_call_id", ""))
        elif event.type == "tool_execution_end":
            self._state.pending_tool_calls.discard(getattr(event, "tool_call_id", ""))
        elif event.type == "turn_end":
            msg = getattr(event, "message", {})
            if msg.get("role") == "assistant" and msg.get("error_message"):
                self._state.error_message = msg.get("error_message")
        elif event.type == "agent_end":
            self._state.streaming_message = None

    async def _run_lifecycle(self, loop_executor: Callable[[AbortSignal], Any]) -> None:
        abort_signal = AbortSignal()
        
        self._state.is_streaming = True
        self._state.streaming_message = None
        self._state.error_message = None
        
        token = _active_agent_ctx.set(self)
        try:
            async def run_task():
                await loop_executor(abort_signal)
                
            task = asyncio.create_task(run_task())
            self.active_run = ActiveRun(task=task, abort_signal=abort_signal)
            
            await task
        finally:
            _active_agent_ctx.reset(token)
            self._finish_run()

    def _finish_run(self):
        self._state.is_streaming = False
        self._state.streaming_message = None
        self._state.pending_tool_calls = set()
        self.active_run = None


# --- Legacy PyAgent Implementation Layer ---

class PyAgent:
    """Backward-compatible runtime wrapper class conforming to legacy PyAgent interfaces."""
    
    def __init__(self, backend: BaseBackend, system_prompt: str, tools: Optional[List[Any]] = None):
        self._agent = Agent(
            backend=backend,
            initial_state={
                "systemPrompt": system_prompt,
                "tools": tools or []
            }
        )
        self.backend = backend
        self.system_prompt = system_prompt
        self.tools = self._agent.state.tools
        self._agent_interrupted = False

    @property
    def history(self) -> List[Dict[str, Any]]:
        return self._agent.state.messages

    @history.setter
    def history(self, val: List[Dict[str, Any]]):
        self._agent.state.messages = val

    @property
    def _interrupted(self) -> bool:
        if self._agent_interrupted:
            return True
        if self._agent.active_run and self._agent.active_run.abort_signal.aborted:
            return True
        return False

    def interrupt(self):
        self._agent_interrupted = True
        self._agent.abort()

    async def run_loop(self, user_prompt: str) -> AsyncGenerator[LegacyAgentEvent, None]:
        """Runs the execution turn yielding legacy AgentEvent compatibility objects."""
        self._agent_interrupted = False
        async for event in self._agent.prompt_stream(user_prompt):
            if event.type == "message_update":
                ev = getattr(event, "assistant_message_event", {})
                if ev.get("type") == "text_delta":
                    yield LegacyAgentEvent(type="text_delta", content=ev["delta"])
            elif event.type == "tool_execution_start":
                yield LegacyAgentEvent(type="tool_start", content=getattr(event, "tool_name", ""))
            elif event.type == "tool_execution_end":
                tname = getattr(event, "tool_name", "")
                res = getattr(event, "result", {})
                
                # Extract text block content
                res_content = res.get("content", [{"type": "text", "text": ""}])
                res_str = ""
                if isinstance(res_content, list) and len(res_content) > 0:
                    res_str = res_content[0].get("text", "")
                else:
                    res_str = str(res_content)
                    
                yield LegacyAgentEvent(type="tool_end", content={"tool": tname, "result": res_str})
            elif event.type == "interrupted":
                yield LegacyAgentEvent(type="interrupted", content=getattr(event, "reason", "Interrupted."))
            elif event.type == "error":
                yield LegacyAgentEvent(type="error", content=getattr(event, "error", "Error occurred."))
            elif event.type == "agent_end":
                # Find last assistant content
                assistant_content = ""
                for msg in reversed(self._agent.state.messages):
                    if msg.get("role") == "assistant":
                        assistant_content = msg.get("content") or ""
                        break
                yield LegacyAgentEvent(type="done", content=assistant_content)
