import asyncio
import sys
import json
import subprocess
from py_agent_core import Agent, DummyBackend, tool
from py_agent_core.backends.base import BackendChunk, ToolCallChunk
from examples.utils import get_backend_from_args

@tool
async def execute_python_code(code: str) -> str:
    """Executes a Python script in an isolated subprocess and returns stdout/stderr.

    Args:
        code: The complete Python source code block to execute.
    """
    print(f"\n--- [Tool: execute_python_code] Executing Code ---")
    print(code)
    print("-------------------------------------------------")
    
    try:
        proc = await asyncio.create_subprocess_exec(
            # Use sys.executable (the current interpreter) rather than "python"
            # so the subprocess inherits the same virtualenv and installed packages
            sys.executable, "-c", code,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            stdout, stderr = await proc.communicate()
            out_str = stdout.decode("utf-8", errors="replace").strip()
            err_str = stderr.decode("utf-8", errors="replace").strip()
            
            result = f"Execution Timeout (Limit: 15 seconds).\n"
            if out_str:
                result += f"\nStandard Output before timeout:\n{out_str}"
            if err_str:
                result += f"\nStandard Error before timeout:\n{err_str}"
            
            print(f"[Tool Result] Timeout:\n{result}\n")
            return result

        exit_code = proc.returncode
        out_str = stdout.decode("utf-8", errors="replace").strip()
        err_str = stderr.decode("utf-8", errors="replace").strip()
        
        result_parts = []
        if exit_code != 0:
            result_parts.append(f"Execution Failed (Exit Code: {exit_code}).")
        else:
            result_parts.append("Execution Succeeded.")
            
        if out_str:
            result_parts.append(f"Standard Output:\n{out_str}")
        if err_str:
            result_parts.append(f"Standard Error / Traceback:\n{err_str}")
            
        if not out_str and not err_str:
            result_parts.append("(No output on stdout or stderr)")
            
        result = "\n\n".join(result_parts)
        
        if exit_code != 0:
            print(f"[Tool Result] Failed:\n{result}\n")
        else:
            print(f"[Tool Result] Succeeded:\n{result}\n")
            
        return result
    except Exception as e:
        return f"Launch Error: {str(e)}"

# Custom DummyBackend subclass to mock the self-healing feedback loop offline
class CoderDummyBackend(DummyBackend):
    async def generate_stream(self, messages, tools=None):
        # Count tool execution results in history
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        
        if not tool_msgs:
            # Turn 1: No tool results yet — agent generates first attempt (with the planted bug)
            bad_code = (
                "def calculate_factorial(n):\n"
                "    if n == 0 or n == 1:\n"
                "        return 1\n"
                "    return n * calculate_factorial(n - 1)\n"
                "print(calculate_factorial(5"  # SyntaxError: unexpected EOF while parsing
            )
            yield BackendChunk(tool_calls=[
                ToolCallChunk(index=0, id="call_1", name="execute_python_code", arguments="")
            ])
            await asyncio.sleep(self.chunk_delay)
            yield BackendChunk(tool_calls=[
                ToolCallChunk(index=0, id="call_1", arguments=json.dumps({"code": bad_code}))
            ])
        elif len(tool_msgs) == 1:
            # Turn 2: One tool result exists; inspect its content to decide whether to retry
            last_result = tool_msgs[0].get("content") or ""
            if "failed" in last_result.lower() or "error" in last_result.lower():
                good_code = (
                    "def calculate_factorial(n):\n"
                    "    if n == 0 or n == 1:\n"
                    "        return 1\n"
                    "    return n * calculate_factorial(n - 1)\n"
                    "print(calculate_factorial(5))"  # Fixed
                )
                yield BackendChunk(tool_calls=[
                    ToolCallChunk(index=0, id="call_2", name="execute_python_code", arguments="")
                ])
                await asyncio.sleep(self.chunk_delay)
                yield BackendChunk(tool_calls=[
                    ToolCallChunk(index=0, id="call_2", arguments=json.dumps({"code": good_code}))
                ])
            else:
                yield BackendChunk(text="The code was executed successfully.")
        else:
            # Turn 3: Report final solution after receiving correct run output
            yield BackendChunk(text=f"The code has run successfully! Output of factorial(5) is 120. I resolved the SyntaxError by closing the parenthesis in print(calculate_factorial(5)).")

async def main():
    backend, model = get_backend_from_args("Self-Healing Developer Loop Demo")
    
    # Swap out base DummyBackend for our turn-based coder simulation
    if isinstance(backend, DummyBackend):
        backend = CoderDummyBackend(chunk_delay=0.01)
        prompt = 'call_tool:execute_python_code:{}' # Seed to start execution
    else:
        prompt = "Write and execute a Python script to calculate the factorial of 5. Test it using execute_python_code."
        
    print(f"Initializing Self-Healing Agent using: {backend.__class__.__name__} ({model})...")
    
    agent = Agent(
        backend=backend,
        initial_state={
            "systemPrompt": (
                "You are an AI developer. Write a python script to solve the task. "
                "You must execute the code using execute_python_code, check for errors, "
                "and if it fails, analyze the traceback to fix the code and rerun it. "
                "IMPORTANT: The execution environment is non-interactive, so you MUST explicitly "
                "print any results/outputs using print() in order to see them."
            ),
            "tools": [execute_python_code]
        }
    )
    
    async for event in agent.prompt_stream(prompt):
        if event.type == "message_update":
            ev = getattr(event, "assistant_message_event", {})
            if ev.get("type") == "text_delta":
                print(ev["delta"], end="", flush=True)
        elif event.type == "tool_execution_start":
            print(f"\n[Agent] Initiating execution of: {event.tool_name}...")
        elif event.type == "tool_execution_end":
            print(f"[Agent] Execution finished.")
        elif event.type == "agent_end":
            final_content = ""
            for msg in reversed(agent.state.messages):
                if msg.get("role") == "assistant":
                    final_content = msg.get("content") or ""
                    break
            print(f"\n\n[Agent Completed Task]\n{final_content}")

if __name__ == "__main__":
    asyncio.run(main())
