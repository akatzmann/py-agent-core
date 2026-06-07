import asyncio
import json
import sys
from py_agent_core import Agent, DummyBackend, tool
from py_agent_core.backends.base import BackendChunk, ToolCallChunk
from examples.utils import get_backend_from_args

# Define tools

@tool
async def run_shell_command(command: str) -> str:
    """Executes a command. Treated as a 'risky' tool requiring approval.

    Args:
        command: The shell command string to execute.
    """
    print(f"\n[Tool: run_shell_command] Running: '{command}'")
    return f"Command '{command}' output: success (mocked)"

@tool
async def slow_fetch_1() -> str:
    """Simulates a slow data fetch from Source 1."""
    print("\n[Tool: slow_fetch_1] Starting fetch...")
    await asyncio.sleep(0.5)
    print("[Tool: slow_fetch_1] Done.")
    return "Data from Source 1"

@tool
async def slow_fetch_2() -> str:
    """Simulates a slow data fetch from Source 2."""
    print("\n[Tool: slow_fetch_2] Starting fetch...")
    await asyncio.sleep(0.5)
    print("[Tool: slow_fetch_2] Done.")
    return "Data from Source 2"


# Custom DummyBackend to simulate advanced agent turn behaviors offline
class AdvancedDummyBackend(DummyBackend):
    async def generate_stream(self, messages, tools=None):
        # We simulate three turns based on message count in history:
        # Turn 1: Requests parallel tools (slow_fetch_1 and slow_fetch_2)
        # Turn 2: Requests risky tool (run_shell_command)
        # Turn 3: Final synthesis
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        
        # Filter messages to count user turns
        user_msgs = [m for m in messages if m.get("role") == "user"]
        
        if len(user_msgs) == 1 and not tool_msgs:
            # Turn 1: Trigger parallel tool execution
            yield BackendChunk(text="Initiating parallel data retrieval. Please wait...\n")
            await asyncio.sleep(self.chunk_delay)
            yield BackendChunk(tool_calls=[
                ToolCallChunk(index=0, id="call_fetch_1", name="slow_fetch_1", arguments="{}"),
                ToolCallChunk(index=1, id="call_fetch_2", name="slow_fetch_2", arguments="{}")
            ])
        elif len(user_msgs) == 1 and len(tool_msgs) == 2:
            # Turn 2: LLM received parallel tool results, now requests a risky tool
            yield BackendChunk(text="Retrieved parallel data successfully. Now executing system setup command...\n")
            await asyncio.sleep(self.chunk_delay)
            yield BackendChunk(tool_calls=[
                ToolCallChunk(index=0, id="call_cmd", name="run_shell_command", arguments=json.dumps({"command": "init_system"}))
            ])
        else:
            # Final Turn: Summarize execution
            yield BackendChunk(text="All steps completed. System successfully initialized and data fetched.")


# 1. Telemetry Subscription Callback (Agent.subscribe)
async def console_audit_logger(event, abort_signal):
    """Subscribed listener callback that prints lifecycle events to the terminal."""
    if event.type == "agent_start":
        print("\n=== [Telemetry: agent_start] Run Initiated ===")
    elif event.type == "turn_start":
        print("\n=== [Telemetry: turn_start] New Turn Started ===")
    elif event.type == "message_start":
        role = event.message.get("role", "unknown")
        print(f"  [Telemetry: message_start] Role: {role}")
    elif event.type == "tool_execution_start":
        print(f"  [Telemetry: tool_execution_start] Hook triggered for: {event.tool_name} (ID: {event.tool_call_id})")
    elif event.type == "tool_execution_end":
        err_flag = " [ERROR]" if event.is_error else ""
        print(f"  [Telemetry: tool_execution_end] Hook finished for: {event.tool_name}{err_flag}")
    elif event.type == "interrupted":
        print(f"  [Telemetry: interrupted] 🚨 Run Aborted! Reason: {event.reason}")
    elif event.type == "agent_end":
        print("\n=== [Telemetry: agent_end] Run Finished successfully ===")


# 2. Before Tool Call Hook (Human-in-the-loop Gate)
async def human_approval_gate(data, abort_signal):
    """Asks for confirmation before executing run_shell_command."""
    tool_call = data["tool_call"]
    tool_name = tool_call["function"]["name"]
    args = data["args"]
    
    if tool_name == "run_shell_command":
        # Auto-approve if in non-interactive environment or test run
        is_interactive = sys.stdin.isatty() and "--non-interactive" not in sys.argv
        if not is_interactive:
            print(f"\n[Gate: before_tool_call] Non-interactive mode: Auto-approving '{tool_name}' with args {args}")
            return {"block": False}
            
        print(f"\n[Gate: before_tool_call] ⚠️ RISKY TOOL DETECTED: {tool_name} with arguments {args}")
        user_input = input("Do you want to allow this tool call? (y/n): ").strip().lower()
        if user_input != 'y':
            print("[Gate: before_tool_call] ❌ Execution Denied by User. Aborting run...")
            return {"block": True, "reason": "User denied command execution."}
            
        print("[Gate: before_tool_call] ✓ Execution Approved by User.")
    return {"block": False}


# 3. After Tool Call Hook (Output Auditor)
async def tool_outcome_auditor(data, abort_signal):
    """Audits tool output before presenting it back to the LLM."""
    tool_name = data["tool_call"]["function"]["name"]
    result = data["result"]
    is_error = data["is_error"]
    
    print(f"  [Gate: after_tool_call] Auditing tool result for '{tool_name}'. Success status: {not is_error}")
    
    # If a command contains 'fatal_error' in output, we terminate the LLM loop early
    content_text = str(result.get("content", ""))
    if "fatal_error" in content_text.lower():
        print("  [Gate: after_tool_call] Detected Fatal Error in output! Injecting terminate=True.")
        return {"terminate": True}
        
    return result


# 4. Context Pipelines (convert_to_llm & transform_context)
def convert_to_llm_pipeline(messages):
    """Maps custom message types (like UI cards) into standard format for LLM backend."""
    llm_msgs = []
    for msg in messages:
        role = msg.get("role")
        if role == "ui-card":
            # Map ui-card to standard user text block
            llm_msgs.append({
                "role": "user",
                "content": f"[Rendered UI Card: {msg.get('content')}]"
            })
        elif role in ("user", "assistant", "system", "tool", "toolResult"):
            llm_msgs.append(msg)
            
    # Normalize toolResult to tool role
    final_msgs = []
    for msg in llm_msgs:
        if msg.get("role") == "toolResult":
            final_msgs.append({
                "role": "tool",
                "tool_call_id": msg.get("tool_call_id"),
                "name": msg.get("name"),
                "content": str(msg.get("content"))
            })
        else:
            final_msgs.append(msg)
    return final_msgs


def transform_context_pipeline(messages, abort_signal):
    """Keeps the context window optimal by keeping only the last 4 messages (excluding system prompt)."""
    system_msg = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]
    
    if len(non_system) > 4:
        print(f"\n[Pipeline: transform_context] Pruning context size from {len(messages)} to {len(system_msg) + 4} messages...")
        non_system = non_system[-4:]
        
    return system_msg + non_system


# Main execution flow
async def main():
    backend, model = get_backend_from_args("Advanced Agent Features Demo")
    
    # Swap out base DummyBackend for our turns simulator
    if isinstance(backend, DummyBackend):
        backend = AdvancedDummyBackend(chunk_delay=0.01)
        
    print(f"Initializing Advanced Agent using: {backend.__class__.__name__} ({model})...")
    
    # Setup Agent with all advanced configuration options
    agent = Agent(
        backend=backend,
        initial_state={
            "systemPrompt": "You are a stateful orchestrator showcasing pipeline features.",
            "tools": [run_shell_command, slow_fetch_1, slow_fetch_2]
        },
        convert_to_llm=convert_to_llm_pipeline,
        transform_context=transform_context_pipeline,
        before_tool_call=human_approval_gate,
        after_tool_call=tool_outcome_auditor,
        tool_execution="parallel"  # Run independent tool calls concurrently
    )
    
    # Subscribe the telemetry logger
    agent.subscribe(console_audit_logger)
    
    # Execute run
    prompt = "Please fetch data from both sources in parallel and then start system setup."
    print(f"\n--- Starting Prompt Turn ---\nPrompt: {prompt}")
    
    # We iterate using the generator stream to render text updates
    async for event in agent.prompt_stream(prompt):
        if event.type == "message_update":
            ev = getattr(event, "assistant_message_event", {})
            if ev.get("type") == "text_delta":
                print(ev["delta"], end="", flush=True)
                
    # 5. Showcasing steering and follow-up queues
    print("\n\n--- Showcasing steering and follow-up ---")
    
    # Inject a user steer prompt while agent is idle (will trigger on next run)
    print("\nEnqueuing follow-up action...")
    agent.follow_up({"role": "user", "content": "Confirm that the final system initialization is completely done."})
    
    print("Enqueuing steer override...")
    agent.steer({"role": "user", "content": "Actually, write a brief final confirmation statement."})
    
    # Resume agent execution to drain queues
    print("\nResuming loop with continue_()...")
    await agent.continue_()
    
    print("\n--- Final Message History in Agent State ---")
    for msg in agent.state.messages:
        content_preview = str(msg.get("content"))
        if len(content_preview) > 80:
            content_preview = content_preview[:77] + "..."
        print(f"Role: {msg.get('role'):<12} | Content: {content_preview}")


if __name__ == "__main__":
    asyncio.run(main())
