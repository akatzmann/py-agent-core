import asyncio
import json
from py_agent_core import PyAgent, DummyBackend
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
        
    agent = PyAgent(backend, system_prompt=system_prompt)
    
    print("\nStreaming tokens from agent:")
    print("----------------------------")
    
    async for event in agent.run_loop("Fetch profile data"):
        if event.type == "text_delta":
            print(event.content, end="", flush=True)
        elif event.type == "done":
            print("\n----------------------------")
            print("Stream finished. Parsing final consolidated output...")
            
            try:
                parsed_data = json.loads(event.content)
                print("\nParsed JSON successfully:")
                print(json.dumps(parsed_data, indent=2))
            except json.JSONDecodeError as e:
                print(f"\nFailed to parse output as JSON. Output was: {event.content!r}")
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
