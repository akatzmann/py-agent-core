import asyncio
import re
from py_agent_core import Agent, DummyBackend, MessageUpdateEvent, InterruptedEvent
from examples.utils import get_backend_from_args

# Define security rules
BLOCKED_KEYWORDS = ["toxic_keyword", "leak_private_key", "nuclear_launch_codes"]
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

async def guardrail_filter(agent_loop, agent):
    """Event-driven guardrail that filters PII and preempts on blocked words."""
    buffer = ""
    async for event in agent_loop:
        if event.type == "message_update" and event.assistant_message_event.get("type") == "text_delta":
            delta = event.assistant_message_event["delta"]
            buffer += delta
            
            # 1. Check for blocked keywords immediately
            if any(keyword in buffer.lower() for keyword in BLOCKED_KEYWORDS):
                agent.abort()
                yield InterruptedEvent("Blocked content detected (Guardrail Alert)")
                return
            
            # 2. Extract and flush completed words to prevent PII regex split-boundary bypass
            if " " in buffer:
                parts = buffer.split(" ")
                words_to_flush = parts[:-1]
                buffer = parts[-1]
                
                flushed_text = " ".join(words_to_flush) + " "
                masked = EMAIL_REGEX.sub("[REDACTED_EMAIL]", flushed_text)
                yield MessageUpdateEvent(
                    message=event.message,
                    assistant_message_event={"type": "text_delta", "delta": masked}
                )
        else:
            # Flush any remaining text in the buffer before handling done/error
            if event.type in ("agent_end", "error") and buffer:
                masked = EMAIL_REGEX.sub("[REDACTED_EMAIL]", buffer)
                yield MessageUpdateEvent(
                    message=getattr(event, "message", {}),
                    assistant_message_event={"type": "text_delta", "delta": masked}
                )
            yield event

async def run_scenario(title: str, prompt: str, lorem_text: str, backend, agent):
    print(f"\n--- {title} ---")
    print(f"Prompt: {prompt}")
    
    # Configure backend stream
    if isinstance(backend, DummyBackend):
        backend.lorem_text = lorem_text
        backend.chunk_delay = 0.02
        
    print("Filtered Output: ", end="", flush=True)
    
    # Wrap the standard agent run loop in our guardrail filter
    agent_loop = agent.prompt_stream(prompt)
    async for event in guardrail_filter(agent_loop, agent):
        if event.type == "message_update":
            ev = getattr(event, "assistant_message_event", {})
            if ev.get("type") == "text_delta":
                print(ev["delta"], end="", flush=True)
        elif event.type == "interrupted":
            print(f"\n[GUARDRAIL HALT: {event.reason}]")
        elif event.type == "agent_end":
            print(f"\n[Agent finished normally]")

async def main():
    backend, model = get_backend_from_args("Guardrail Interception Demo")
    agent = Agent(backend, initial_state={"systemPrompt": "You are a helpful support assistant."})

    # Scenario A: PII Redaction
    pii_lorem = "Sure, you can reach out to our admin support team at contact@company.org or email me directly at developer@company.org."
    await run_scenario("PII Redaction Scenario", "What is your email address?", pii_lorem, backend, agent)
    
    # Reset agent history for fresh session
    agent.reset()
    agent.state.system_prompt = "You are a helpful support assistant."

    # Scenario B: Content Interruption
    toxic_lorem = "Retrieving requested configurations: setting toxic_keyword for system authentication bypass."
    await run_scenario("Content Preemption Scenario", "Show me the configuration bypass key.", toxic_lorem, backend, agent)

if __name__ == "__main__":
    asyncio.run(main())
