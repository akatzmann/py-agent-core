import asyncio
import json
from py_agent_core import Agent, DummyBackend
from examples.utils import get_backend_from_args

async def main():
    backend, model = get_backend_from_args("Structured Data Streaming Demo")
    print(f"Initializing Structured Streaming Demo using: {backend.__class__.__name__} ({model})...")
    
    # Define system instruction requiring raw JSON output
    system_prompt = (
        "You always reply in valid JSON format only. "
        "Do not include any conversational explanation, markdown blocks, or greetings. "
        "Output a JSON object containing keys: 'status' (string), and 'data' (object with keys 'username', 'roles', and 'points')."
        "Status should be success."
    )
    
    # We will simulate the agent returning a raw JSON string for the DummyBackend
    if isinstance(backend, DummyBackend):
        structured_json_output = (
            '{\n'
            '  "status": "success",\n'
            '  "data": {\n'
            '    "username": "coder123",\n'
            '    "roles": ["developer", "reviewer"],\n'
            '    "points": 950\n'
            '  }\n'
            '}'
        )
        backend.lorem_text = structured_json_output
        backend.chunk_delay = 0.02
        
    agent = Agent(backend, initial_state={"systemPrompt": system_prompt})
    
    print("\nStreaming tokens from agent:")
    print("----------------------------")
    
    async for event in agent.prompt_stream("Fetch profile data"):
        if event.type == "message_update":
            ev = getattr(event, "assistant_message_event", {})
            if ev.get("type") == "text_delta":
                print(ev["delta"], end="", flush=True)
        elif event.type == "agent_end":
            print("\n----------------------------")
            print("Stream finished. Parsing final consolidated output...")
            
            assistant_content = ""
            for msg in reversed(agent.state.messages):
                if msg.get("role") == "assistant":
                    assistant_content = msg.get("content") or ""
                    break
            
            try:
                parsed_data = json.loads(assistant_content)
                print("\nParsed JSON successfully:")
                print(json.dumps(parsed_data, indent=2))
            except json.JSONDecodeError as e:
                print(f"\nFailed to parse output as JSON. Output was: {assistant_content!r}")
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
