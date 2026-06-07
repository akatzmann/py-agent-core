import asyncio
import sys
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition

from py_agent_core import Agent, DummyBackend
from examples.utils import get_backend_from_args

# Global state to keep track of active agent and UI components
active_agent = None

async def run_agent_loop(prompt: str, agent: Agent, output_field: TextArea, status_control: FormattedTextControl, app: Application):
    global active_agent
    active_agent = agent
    status_control.text = "STATUS: Streaming (Press any key to interrupt)..."
    app.invalidate()

    output_field.text += f"\nUser: {prompt}\nAgent: "
    output_field.buffer.cursor_position = len(output_field.text)
    app.invalidate()

    try:
        async for event in agent.prompt_stream(prompt):
            if event.type == "message_update":
                ev = getattr(event, "assistant_message_event", {})
                if ev.get("type") == "text_delta":
                    output_field.text += ev["delta"]
                    output_field.buffer.cursor_position = len(output_field.text)
                    app.invalidate()
            elif event.type == "interrupted":
                output_field.text += f"\n[Interrupted: {event.reason}]\n"
                output_field.buffer.cursor_position = len(output_field.text)
                app.invalidate()
                break
            elif event.type == "agent_end":
                output_field.text += "\n"
                output_field.buffer.cursor_position = len(output_field.text)
                app.invalidate()
    except Exception as e:
        output_field.text += f"\nError: {e}\n"
        output_field.buffer.cursor_position = len(output_field.text)
        app.invalidate()
    finally:
        active_agent = None
        status_control.text = "STATUS: Idle"
        app.invalidate()

def build_tui():
    # Setup backend
    backend, model = get_backend_from_args("Interactive Chat TUI")
    
    # Configure DummyBackend with long streaming content and delay for preemption testing
    if isinstance(backend, DummyBackend):
        backend.lorem_text = (
            "Quantum mechanics is a fundamental theory in physics that describes the physical properties of nature "
            "at the scale of atoms and subatomic particles. It is the foundation of all quantum physics including "
            "quantum chemistry, quantum field theory, quantum technology, and quantum information science. "
            "Classical physics, the description of physics that existed before the theory of relativity and quantum mechanics, "
            "describes many aspects of nature at an ordinary scale, while quantum mechanics explains the aspects of nature "
            "that classical physics cannot explain."
        )
        backend.chunk_delay = 0.08  # Slow chunk delay so interruption is easy to trigger

    agent = Agent(backend, initial_state={"systemPrompt": "You are a helpful and detailed assistant."})

    # UI Widgets
    output_field = TextArea(read_only=True, scrollbar=True, focusable=False)
    output_field.text = "=== PyAgent Interactive Chat TUI ===\nType your query at the bottom and press Enter.\nIf the agent is streaming, press ANY key to interrupt it.\n\n"
    
    input_field = TextArea(multiline=False, height=1, prompt="> ")
    status_control = FormattedTextControl("STATUS: Idle")

    # Layout
    layout = HSplit([
        Window(FormattedTextControl(" PyAgent Interactive Chat TUI"), height=1, style="bg:#00aa00 fg:#ffffff"),
        output_field,
        Window(height=1, char="-"),
        Window(status_control, height=1, style="fg:#ffaa00"),
        input_field,
    ])

    # Key Bindings
    kb = KeyBindings()

    # Condition: Active agent is currently streaming
    is_streaming = Condition(lambda: active_agent is not None)

    # 1. Submit query (when idle)
    @kb.add("enter")
    def _(event):
        if active_agent is None:
            prompt = input_field.text.strip()
            if prompt:
                input_field.text = ""
                # Start agent execution in a background task
                asyncio.create_task(run_agent_loop(prompt, agent, output_field, status_control, event.app))

    # 2. Keypress preemption: Interrupt active stream if any key is pressed
    @kb.add("<any>", filter=is_streaming)
    def _(event):
        global active_agent
        if active_agent:
            active_agent.abort()

    # 3. Quit
    @kb.add("c-c")
    def _(event):
        event.app.exit()

    app = Application(
        layout=Layout(layout, focused_element=input_field),
        key_bindings=kb,
        full_screen=True,
        mouse_support=True,
    )

    return app

if __name__ == "__main__":
    app = build_tui()
    app.run()
