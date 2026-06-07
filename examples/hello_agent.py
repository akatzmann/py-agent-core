import asyncio
from py_agent_core import Agent
from examples.utils import get_backend_from_args

async def main():
    # Get the backend dynamically from CLI args (defaults to DummyBackend offline)
    backend, model = get_backend_from_args("Hello Agent Quickstart Demo")
    
    # Instantiate the agent with a system prompt
    agent = Agent(backend, initial_state={"systemPrompt": "You are a helpful and brief assistant."})
    
    print("Prompt: Hello! Introduce yourself.")
    print("Response: ", end="", flush=True)
    
    # Run the main async loop and print streaming response deltas
    async for event in agent.prompt_stream("Hello! Introduce yourself."):
        if event.type == "message_update":
            ev = getattr(event, "assistant_message_event", {})
            if ev.get("type") == "text_delta":
                print(ev["delta"], end="", flush=True)
        elif event.type == "agent_end":
            assistant_content = ""
            for msg in reversed(agent.state.messages):
                if msg.get("role") == "assistant":
                    assistant_content = msg.get("content") or ""
                    break
            print(f"\n[Finished. Consolidated Answer: '{assistant_content.strip()}']")

if __name__ == "__main__":
    asyncio.run(main())
