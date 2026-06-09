import asyncio
import time
from py_agent_core import Agent, tool, DummyBackend
from examples.utils import get_backend_from_args

# Custom DummyBackend to simulate realistic second-turn response on tool result arrival
class BackgroundDemoDummyBackend(DummyBackend):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.original_lorem = self.lorem_text

    async def generate_stream(self, messages, tools=None):
        # If the history contains a toolResult, return a specific text summarizing the result
        has_tool_res = any(m.get("role") in ("tool", "toolResult") for m in messages)
        if has_tool_res:
            # Look up the tool result content
            tool_content = ""
            for m in reversed(messages):
                if m.get("role") in ("tool", "toolResult"):
                    tool_content = str(m.get("content", ""))
                    break
            self.lorem_text = (
                f"I have received the completed report search results from the background job: {tool_content}. "
                "Based on this data, the project is progressing on track."
            )
        else:
            self.lorem_text = self.original_lorem
            
        async for chunk in super().generate_stream(messages, tools):
            yield chunk

# Define a tool with execution_mode="background"
@tool(execution_mode="background")
async def fetch_long_report(report_id: str) -> str:
    """Fetch a detailed system report. This operation is long-running."""
    print(f"\n[Background Tool] Starting long report fetch for {report_id}...")
    
    # Simulate a 4-second background process with progress updates
    for i in range(1, 5):
        await asyncio.sleep(1)
        print(f"[Background Tool] Fetching report {report_id}... {i*25}% done")
        
    print(f"[Background Tool] Report fetch finished for {report_id}!")
    return f"Report {report_id} Data: [CPU: 12%, Memory: 45%, Disk: 22%]"

@tool
async def sleep(duration: int = 10):
    """Sleep for a specified duration.
    
    Args:
        duration: The duration to sleep in seconds. Default is 10.
    """
    duration = int(duration)
    print(f"\n[Sleep Tool] Starting sleep for {duration} seconds...")
    await asyncio.sleep(duration)
    print(f"[Sleep Tool] Sleep finished for {duration} seconds!")
    return f"Sleep finished for {duration} seconds!"

async def main():
    # Setup backend
    backend, model = get_backend_from_args("Background Tool Execution Demo")
    
    # If DummyBackend is chosen (default), wrap it with our custom simulator
    if isinstance(backend, DummyBackend):
        backend = BackgroundDemoDummyBackend(
            lorem_text="I will look that up for you using the background search tool.",
            chunk_delay=0.02
        )
        
    agent = Agent(backend, initial_state={"systemPrompt": "You are a helpful monitoring assistant."})
    agent.state.tools = [fetch_long_report, sleep]

    # Prompt the agent to run the background tool
    # Using the 'call_tool:...' syntax for DummyBackend matching, or plain language for real models
    prompt = """
    1) Greet the user.
    2) Then, call fetch_long_report with id r-99.
    3) As long as the fetch_long_report tool runs in background, sleep for 10 seconds.
    4) Once that the fetch_long_report tool has completed, inform the user about the report content.
    5) Only finish once that the fetch_long_report tool has completed. If not, sleep again.
    """
    
    print(f"=== Starting Turn 1 (Triggering Background Tool) ===")
    print(f"Prompt: {prompt}\n")
    
    # Start the stream and print the streaming response deltas
    print("Agent Response: ", end="", flush=True)
    async for event in agent.prompt_stream(prompt):
        if event.type == "message_update":
            ev = getattr(event, "assistant_message_event", {})
            if ev.get("type") == "text_delta":
                print(ev["delta"], end="", flush=True)
    print("\n")

if __name__ == "__main__":
    asyncio.run(main())
