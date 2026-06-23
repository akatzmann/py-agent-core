## Context

The repository's current `README.md` has all the basic sections but suffers from:
1. High cognitive load for humans due to the "Skip Reading" prompt block being at the very top.
2. Lack of quick technical comparison to alternative frameworks (LangChain, AutoGen).
3. Gated quickstart requiring OpenAI/Azure API keys and connection setup.
4. Missing visual model explaining the core feature of the library: cooperative transport-level preemption.

## Goals / Non-Goals

**Goals:**
- Present a clear visual diagram explaining the preemption model.
- Restructure the introduction to place the core pitch and value proposition first.
- Reorganize the "Skip Reading" (context delegation) prompts into a clean, visually distinct card format below the fold but highly visible.
- Add a comparative capabilities matrix with UTF-8 icons comparing `py-agent-core` against heavy agent frameworks.
- Simplify the quickstart to run locally out-of-the-box using Ollama.
- Restore and clarify the project's design heritage in relation to `pi-agent-core`.

**Non-Goals:**
- Changing any core Python logic or library backends.
- Updating other repository files (e.g., `CONTRIBUTING.md`, issue templates) that are not the root `README.md`.

## Decisions

### Decision 1: Relocate and Style the Context Delegation Box
- **Choice:** Place the AI Agent context delegation box immediately below the introductory pitch.
- **Rationale:** Keeping it at the top is a great pattern interrupt for high engagement, but wrapping it in an `[!IMPORTANT]` alert box ensures it looks like a premium, styled element rather than plain text, preventing visual clutter for human readers.
- **Alternatives Considered:** 
  - *Moving to the bottom:* Rejected because it reduces visibility for LLM agents scanning the repo.
  - *Using a separate file:* Rejected because agents look at the main `README.md` first.

### Decision 2: Local-First Ollama Quickstart
- **Choice:** Use `OllamaBackend(model="llama3")` in the primary quickstart code block.
- **Rationale:** Ollama requires no API keys and runs locally, lowering the barrier to try the package to zero.
- **Alternatives Considered:**
  - *OpenAI/Azure OpenAI:* Rejected because API keys gate the quickstart experience.
  - *DummyBackend:* Rejected because running a mock doesn't feel like a real agent experience to first-time human readers.

### Decision 3: UTF-8 Capability Matrix
- **Choice:** Implement a Markdown comparison table listing key USPs (Control flow, Preemption, Tool Spec, Model Resilience, Swarm Hierarchy, Bloat) with UTF-8 indicators.
- **Rationale:** Visual checkmarks (`✅`, `❌`, `⚠️`) allow developers to scan comparison features in less than 2 seconds, triggering positive validation.

## Risks / Trade-offs

- **[Risk]** Users might not have Ollama installed or running locally.  
  → **[Mitigation]** Explicitly note in the quickstart code comment that it runs completely offline, and keep the "Swapping LLM Backends" section clear with `AsyncOpenAI` and `DummyBackend` options immediately below the quickstart.
