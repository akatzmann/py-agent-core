import asyncio
from py_agent_core import Agent, DummyBackend
from examples.utils import get_backend_from_args

async def stream_agent(name: str, agent_loop) -> str:
    """Helper to consume an agent event stream and print buffered chunks with prefixes."""
    buffer = ""
    final_output = ""
    
    async for event in agent_loop:
        if event.type == "message_update":
            ev = getattr(event, "assistant_message_event", {})
            if ev.get("type") == "text_delta":
                buffer += ev["delta"]
                # Print output line-by-line to preserve structure while showing concurrency
                if "\n" in buffer:
                    lines = buffer.split("\n")
                    for line in lines[:-1]:
                        if line.strip():
                            print(f"[{name}] {line.strip()}")
                    buffer = lines[-1]
        elif event.type == "agent_end":
            # Find the consolidated answer in events
            for msg in reversed(event.messages):
                if msg.get("role") == "assistant":
                    final_output = msg.get("content") or ""
                    break
            if buffer.strip():
                print(f"[{name}] {buffer.strip()}")
            print(f"[{name} Completed]")
            
    return final_output

async def main():
    # Setup shared or independent backends
    backend, model = get_backend_from_args("Collaborative Agent Swarm Demo")
    
    # Setup worker agents
    researcher = Agent(backend, initial_state={"systemPrompt": "You are a factual research assistant."})
    outliner = Agent(backend, initial_state={"systemPrompt": "You are an editorial outliner who drafts document structures."})
    
    # Configure mock responses if using DummyBackend
    if isinstance(backend, DummyBackend):
        # We need distinct mock backends to run them concurrently with different texts
        research_backend = DummyBackend(
            lorem_text="Fact 1: Fusion energy generates zero greenhouse gases.\nFact 2: It uses abundant fuel sources (hydrogen isotopes).\nFact 3: Commercial deployment is targeted for the 2030s.",
            chunk_delay=0.04
        )
        outline_backend = DummyBackend(
            lorem_text="I. Introduction to Fusion Energy.\nII. Core Engineering Obstacles.\nIII. Financial and Environmental Outlook.",
            chunk_delay=0.06
        )
        researcher = Agent(research_backend, initial_state={"systemPrompt": researcher.state.system_prompt})
        outliner = Agent(outline_backend, initial_state={"systemPrompt": outliner.state.system_prompt})

    research_prompt = "Find 3 key facts about nuclear fusion breakthroughs."
    outline_prompt = "Draft a 3-section outline for a report on fusion power."

    print("=== Phase 1: Running Research and Outline in Parallel ===")
    
    # Spawn tasks concurrently
    research_task = asyncio.create_task(stream_agent("Researcher", researcher.prompt_stream(research_prompt)))
    outline_task = asyncio.create_task(stream_agent("Outliner", outliner.prompt_stream(outline_prompt)))
    
    # Wait for both workers to finish
    research_result, outline_result = await asyncio.gather(research_task, outline_task)
    
    print("\n=== Phase 2: Running Synthesizer Agent to Compile Report ===")
    
    # Setup coordinator/synthesizer agent
    synthesizer = Agent(backend, initial_state={"systemPrompt": "You are a report writer who compiles researcher facts and outline structures into markdown."})
    if isinstance(backend, DummyBackend):
        compiled_markdown = (
            "# Fusion Power: The Future of Clean Energy\n\n"
            "## 1. Introduction to Fusion Energy\n"
            "Fusion energy generates zero greenhouse gases. It is safe and produces no long-lived nuclear waste.\n\n"
            "## 2. Core Engineering Obstacles\n"
            "Abundant fuel sources like hydrogen isotopes require extreme magnetic confinement devices (tokamaks).\n\n"
            "## 3. Financial and Environmental Outlook\n"
            "Commercial deployment targets the 2030s, revolutionizing global clean electricity grids."
        )
        synth_backend = DummyBackend(lorem_text=compiled_markdown, chunk_delay=0.02)
        synthesizer = Agent(synth_backend, initial_state={"systemPrompt": synthesizer.state.system_prompt})

    synth_prompt = (
        f"Compile the following research facts and outline structure into a clean markdown document.\n\n"
        f"Research:\n{research_result}\n\nOutline:\n{outline_result}"
    )
    
    print("[Synthesizer] Compiling final report...")
    final_report = await stream_agent("Synthesizer", synthesizer.prompt_stream(synth_prompt))
    
    print("\n=== Final Markdown Generated ===")
    print(final_report)

if __name__ == "__main__":
    asyncio.run(main())
