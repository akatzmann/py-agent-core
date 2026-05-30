import asyncio
from py_agent_core import PyAgent, DummyBackend, tool
from examples.utils import get_backend_from_args

# Define a slow search tool
@tool
async def slow_search(query: str) -> str:
    """Runs a mock search query that takes some time.

    Args:
        query: The search terms.
    """
    print(f"\n[Tool] Starting slow_search for: '{query}'...")
    # Sleep for 3 seconds to simulate a slow backend call
    await asyncio.sleep(3.0)
    print(f"[Tool] slow_search completed for: '{query}'.")
    return f"Mock search results for: '{query}'"

async def watchdog_timer(agent: PyAgent, max_execution_time: float):
    """Asynchronous watchdog that interrupts the agent after a timeout."""
    await asyncio.sleep(max_execution_time)
    print(f"\n[Watchdog] Execution limit of {max_execution_time}s reached! Interrupting...")
    agent.interrupt()

async def main():
    backend, model = get_backend_from_args("Watchdog Timeout Interruption Demo")
    print(f"Initializing Watchdog Demo using: {backend.__class__.__name__} ({model})...")
    
    agent = PyAgent(
        backend=backend,
        system_prompt="You are a helpful assistant who always runs slow_search when asked to find information.",
        tools=[slow_search]
    )
    
    if isinstance(backend, DummyBackend):
        # Format the prompt to call the tool inside DummyBackend
        prompt = 'call_tool:slow_search:{"query": "deep learning advancements"}'
    else:
        prompt = "Please search the web for 'deep learning advancements'."
        
    # Spawn the watchdog task with a 1.0 second timeout limit
    # This is much shorter than the 3.0 second tool run time, so it will trigger!
    watchdog_task = asyncio.create_task(watchdog_timer(agent, max_execution_time=1.0))
    
    print(f"[Parent] Running loop with 1.0s watchdog limit...")
    interrupted = False
    
    try:
        async for event in agent.run_loop(prompt):
            if event.type == "text_delta":
                print(event.content, end="", flush=True)
            elif event.type == "tool_start":
                print(f"\n[Parent] Tool execution started: '{event.content}'")
            elif event.type == "tool_end":
                print(f"\n[Parent] Tool execution completed: '{event.content['tool']}'")
            elif event.type == "interrupted":
                print(f"\n[Parent] Agent reported interruption event: {event.content}")
                interrupted = True
                break
            elif event.type == "done":
                print(f"\n[Parent] Agent completed task normally: {event.content}")
    finally:
        # Clean up the watchdog task
        watchdog_task.cancel()
    
    if interrupted:
        print("\nDemo Succeeded: Watchdog successfully aborted the agent mid-execution!")
    else:
        print("\nDemo Completed: Agent execution finished before watchdog triggered.")

if __name__ == "__main__":
    asyncio.run(main())
