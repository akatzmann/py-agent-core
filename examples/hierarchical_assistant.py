import asyncio
from py_agent_core import PyAgent, DummyBackend, tool
from examples.utils import get_backend_from_args

# Global variables to share the parsed backend across sub-agent tools
CURRENT_BACKEND = None
CURRENT_MODEL = None

@tool
async def code_writer(task: str) -> str:
    """Delegates code writing to a specialized developer sub-agent.

    Args:
        task: Detailed description of the function or script to write.
    """
    print(f"\n---> [Sub-Agent: code_writer] Started writing code for task: '{task}'")
    
    if isinstance(CURRENT_BACKEND, DummyBackend):
        written_code = (
            "def calculate_factorial(n):\n"
            "    if n == 0 or n == 1:\n"
            "        return 1\n"
            "    return n * calculate_factorial(n - 1)"
        )
        sub_backend = DummyBackend(lorem_text=written_code, chunk_delay=0.01)
        prompt = task
    else:
        sub_backend = CURRENT_BACKEND
        prompt = f"Write Python code for the following task. Output only the raw code without explanations:\n{task}"
        
    sub_agent = PyAgent(sub_backend, system_prompt="You are a Python coding sub-agent.")
    
    final_code = ""
    async for event in sub_agent.run_loop(prompt):
        if event.type == "text_delta":
            print(event.content, end="", flush=True)
        elif event.type == "done":
            final_code = event.content
            
    print("\n---> [Sub-Agent: code_writer] Finished code generation.")
    return final_code

@tool
async def code_reviewer(code: str) -> str:
    """Delegates verification and review of written code to a reviewer sub-agent.

    Args:
        code: The Python source code to review.
    """
    print(f"\n---> [Sub-Agent: code_reviewer] Reviewing the code:\n{code}")
    
    if isinstance(CURRENT_BACKEND, DummyBackend):
        review_comments = "Code Quality: Excellent. Recursion is base-cased correctly. Time Complexity: O(n). Review Status: APPROVED."
        sub_backend = DummyBackend(lorem_text=review_comments, chunk_delay=0.01)
        prompt = code
    else:
        sub_backend = CURRENT_BACKEND
        prompt = f"Review the following python code for errors and clean style. Provide a brief one-line review:\n{code}"
        
    sub_agent = PyAgent(sub_backend, system_prompt="You are a code reviewer sub-agent.")
    
    final_review = ""
    async for event in sub_agent.run_loop(prompt):
        if event.type == "text_delta":
            print(event.content, end="", flush=True)
        elif event.type == "done":
            final_review = event.content
            
    print("\n---> [Sub-Agent: code_reviewer] Finished review.")
    return final_review

async def main():
    global CURRENT_BACKEND, CURRENT_MODEL
    CURRENT_BACKEND, CURRENT_MODEL = get_backend_from_args("Hierarchical Coordinator Agent Demo")
    
    print(f"Initializing Hierarchical Coordinator Agent using: {CURRENT_BACKEND.__class__.__name__} ({CURRENT_MODEL})...")
    
    parent_agent = PyAgent(
        backend=CURRENT_BACKEND,
        system_prompt=(
            "You are a manager agent supervising code tasks. You MUST write a function using code_writer, "
            "review it using code_reviewer, and then state the final output to the user."
        ),
        tools=[code_writer, code_reviewer]
    )
    
    if isinstance(CURRENT_BACKEND, DummyBackend):
        # Format the user prompt to trigger a mock tool call sequence in DummyBackend
        prompt = 'call_tool:code_writer:{"task": "factorial function in Python"}'
    else:
        prompt = "Please write a factorial function in Python, get it reviewed, and summarize the result."
        
    print(f"\n[Parent] Sending task prompt: '{prompt}'")
    
    async for event in parent_agent.run_loop(prompt):
        if event.type == "text_delta":
            print(event.content, end="", flush=True)
        elif event.type == "tool_start":
            print(f"\n[Parent] Executing sub-agent tool: '{event.content}'")
        elif event.type == "tool_end":
            print(f"\n[Parent] Tool completed. Returned value:\n{event.content['result']}")
        elif event.type == "done":
            print(f"\n[Parent] Task Complete. final answer:\n{event.content}")

if __name__ == "__main__":
    asyncio.run(main())
