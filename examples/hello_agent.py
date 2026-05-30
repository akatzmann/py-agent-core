import asyncio
from py_agent_core import PyAgent
from examples.utils import get_backend_from_args

async def main():
    # Get the backend dynamically from CLI args (defaults to DummyBackend offline)
    backend, model = get_backend_from_args("Hello Agent Quickstart Demo")
    
    # Instantiate the agent with a system prompt
    agent = PyAgent(backend, system_prompt="You are a helpful and brief assistant.")
    
    print("Prompt: Hello! Introduce yourself.")
    print("Response: ", end="", flush=True)
    
    # Run the main async loop and print streaming response deltas
    async for event in agent.run_loop("Hello! Introduce yourself."):
        if event.type == "text_delta":
            print(event.content, end="", flush=True)
        elif event.type == "done":
            print(f"\n[Finished. Consolidated Answer: '{event.content.strip()}']")

if __name__ == "__main__":
    asyncio.run(main())
