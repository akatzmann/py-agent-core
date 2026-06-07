import asyncio
import sys
from py_agent_core import Agent, DummyBackend
from examples.utils import get_backend_from_args

# Dummy text database for offline simulation
LOREM_ORATIONS = {
    "Ancient Rome": (
        "Ancient Rome was a civilization that grew from a small agricultural community founded on the Italian Peninsula. "
        "Over the centuries, it transformed into an almighty empire dominating the Mediterranean basin through sheer force, "
        "sophisticated military tactics, and highly organized engineering marvels like aqueducts and paved roads. "
        "Its laws, architecture, and political systems laid the bedrock of Western civilization."
    ),
    "Bird Migration": (
        "Interestingly, long before Romans built their roads, nature established its own global networks. "
        "Bird migration patterns span thousands of miles across continents, guiding flocks via Earth's magnetic fields and stellar maps. "
        "This incredible seasonal journey shows the marvelous coordination inherent in biological systems."
    ),
    "Quantum Physics": (
        "Just as birds navigate large macro-worlds, subatomic particles exist in a state of endless probability. "
        "Quantum physics teaches us that particles can exist in superposition, defying classical mechanics entirely. "
        "Reality, at its most fundamental level, is not deterministic, but probabilistic and wave-like."
    )
}

DEFAULT_ORATION = (
    "Transitioning now to the newly requested topic. Life and nature teach us that adaptability is the key to progress. "
    "Every topic is interconnected if we look closely enough at the patterns that govern information and reality."
)

async def input_listener(agent_context: dict):
    loop = asyncio.get_running_loop()
    while True:
        try:
            user_input = await loop.run_in_executor(None, sys.stdin.readline)
            new_topic = user_input.strip()
            if new_topic:
                agent_context["pending_topic"] = new_topic
                if agent_context["agent"]:
                    agent_context["agent"].abort()
        except Exception:
            break

async def speaker_loop(agent_context: dict, backend, model: str):
    current_topic = "Ancient Rome"
    print(f"Orator starting with backend: {backend.__class__.__name__} ({model}). Current Topic: '{current_topic}'.")
    print("Type a new topic at any time and press Enter to interrupt and transition!\n")
    print("Orator: ", end="", flush=True)
    
    # Store history for live backends to keep context across speaking turns
    live_history = []
    
    while True:
        # Resolve prompt and backend setup
        if isinstance(backend, DummyBackend):
            text_to_speak = LOREM_ORATIONS.get(current_topic, DEFAULT_ORATION)
            backend.lorem_text = text_to_speak
            backend.chunk_delay = 0.04
            prompt = f"Speak about {current_topic}"
        else:
            prompt = (
                f"Continue the monologue about {current_topic}. "
                f"Generate only the next short paragraph (1-2 sentences). "
                f"Do not greet the user, just continue speaking. Maintain rhetorical continuity."
            )
            
        # Instantiate a new Agent for this turn
        agent = Agent(
            backend=backend,
            initial_state={
                "systemPrompt": f"You are a continuous rhetoric speaker talking about: {current_topic}. Generate short, elegant chunks."
            }
        )
        if live_history:
            agent.state.messages = list(live_history)
            
        agent_context["agent"] = agent

        interrupted = False
        async for event in agent.prompt_stream(prompt):
            if event.type == "message_update":
                ev = getattr(event, "assistant_message_event", {})
                if ev.get("type") == "text_delta":
                    print(ev["delta"], end="", flush=True)
            elif event.type == "interrupted":
                interrupted = True
                break
        
        if interrupted:
            # Topic changed!
            new_topic = agent_context.get("pending_topic", "General")
            print(f"\n\n[INTERRUPTED! Phrasing transition to: '{new_topic}']\n")
            print("Orator: ", end="", flush=True)
            
            # Print transition bridge
            print(f"Speaking of {current_topic}, it leads us naturally to think of another concept: {new_topic}. ", end="", flush=True)
            await asyncio.sleep(0.5)
            
            # Set the new topic and clear pending
            current_topic = new_topic
            agent_context["pending_topic"] = None
            
            # Clear or seed transition in history
            live_history = [{"role": "system", "content": f"You are a speaker who just transitioned to {current_topic}."}]
        else:
            # Save history state for continuous generation on next turn
            live_history = agent.state.messages
            print(" ", end="", flush=True)
            await asyncio.sleep(1.5)

async def main():
    backend, model = get_backend_from_args("Rhetoric Speaker Monologue Demo")
    agent_context = {"agent": None, "pending_topic": None}
    
    try:
        await asyncio.gather(
            speaker_loop(agent_context, backend, model),
            input_listener(agent_context)
        )
    except KeyboardInterrupt:
        print("\nExiting Orator.")

if __name__ == "__main__":
    asyncio.run(main())
