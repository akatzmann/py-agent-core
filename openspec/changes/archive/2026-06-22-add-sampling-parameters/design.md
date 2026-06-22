## Context

Currently, the `BaseBackend` abstract base class and concrete backend adapters (`OpenAIBackend`, `OllamaBackend`, `AzureOpenAIBackend`) do not accept standard sampling configuration settings such as `temperature` and `top_p` during initialization. Adding these settings to the backend adapters allows developers to configure generation parameters directly on backend initialization, aligning with the TS `@earendil-works/pi-agent-core` reference architecture where generation options belong to the model provider layer rather than the agent's stateful loop.

## Goals / Non-Goals

**Goals:**
- Update `BaseBackend` and concrete backend classes to accept `temperature` and `top_p` in their constructors, storing them as instance properties.
- Ensure these parameters are forwarded to the underlying SDK calls (`AsyncOpenAI.chat.completions.create`, `AsyncClient.chat`, `AsyncAzureOpenAI.chat.completions.create`) if they are configured (i.e., not `None`).
- Update `examples/utils.py` to parse `--temperature` and `--top-p` and pass them to backend constructors.

**Non-Goals:**
- Exposing sampling parameters directly in the `Agent` class constructor or `AgentState` configuration to prevent leaking LLM-specific parameters into the core runner loop.
- Supporting more specialized/niche parameters like `frequency_penalty`, `presence_penalty`, or `top_k` in this change.

## Decisions

- **Decision 1: Store parameters as instance variables in backends**
  - *Alternatives considered:* Passing sampling parameters dynamically to the `agent.prompt` or `agent.prompt_stream` methods.
  - *Rationale:* The `Agent` loop is decoupled from backend-specific sampling controls. Setting these on the backend instance keeps the high-level `Agent` orchestration API completely clean.
- **Decision 2: Pass parameters only if explicitly set (non-None)**
  - *Alternatives considered:* Providing hardcoded defaults in our backend wrappers (e.g., `temperature=0.7` or `1.0`).
  - *Rationale:* Keeping parameters as `None` by default and only passing them if they are configured allows the underlying model provider (Ollama / OpenAI / Azure) to use its own default behavior, avoiding compatibility issues with models that have specific sampling constraints.
- **Decision 3: Handle Ollama `options` dictionary wrapping**
  - *Rationale:* The Ollama SDK requires parameters like `temperature` and `top_p` to be wrapped inside an `options` dictionary parameter (e.g., `options={"temperature": 0.7}`). The `OllamaBackend.generate_stream` method must build this structure dynamically.

## Risks / Trade-offs

- [SDK Validation Error] → Passing invalid sampling ranges (e.g., `temperature` outside [0, 2]) will result in API/SDK exceptions.
  - *Mitigation:* We will let the underlying SDK/API validations handle bounds checking and bubble up any validation errors as standard exceptions.
