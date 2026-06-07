import asyncio
import sys
from py_agent_core import Agent, tool
from examples.utils import get_backend_from_args

# --- Tool definition ---

@tool
async def run_python_code(code: str) -> str:
    """Executes a Python code snippet and returns its output (stdout/stderr).

    Args:
        code: The Python source code to run.
    """
    # Ask the human before running anything — non-blocking via thread
    answer = await asyncio.to_thread(input, f"\n[Tool] Run this code?\n\n{code}\n\nApprove? [y/N]: ")
    if answer.strip().lower() != "y":
        return "User declined execution."

    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-c", code,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    out = stdout.decode().strip()
    err = stderr.decode().strip()
    return f"Output:\n{out}" if not err else f"Output:\n{out}\nError:\n{err}"

# --- Agent setup and main loop ---

async def main():
    backend, model = get_backend_from_args("Minimal Coder Demo")
    suggestion = "What is the factorial of 12?"
    raw = input(f"Task [{suggestion}]: ").strip()
    task = raw or suggestion

    agent = Agent(backend, initial_state={
        "systemPrompt": "You are a coding assistant. Solve the user's task by writing and running Python code.",
        "tools": [run_python_code],
    })

    print("\nAgent: ", end="", flush=True)
    async for event in agent.prompt_stream(task):
        if event.type == "message_update":
            ev = getattr(event, "assistant_message_event", {})
            if ev.get("type") == "text_delta":
                print(ev["delta"], end="", flush=True)
        elif event.type == "agent_end":
            print("\n[Done]")

if __name__ == "__main__":
    asyncio.run(main())
