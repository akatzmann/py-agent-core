## 1. Backend Implementations

- [x] 1.1 Update `BaseBackend` constructor in `py_agent_core/backends/base.py` to accept `temperature` and `top_p`.
- [x] 1.2 Update `OpenAIBackend` constructor and SDK call parameter mapping in `py_agent_core/backends/openai.py`.
- [x] 1.3 Update `AzureOpenAIBackend` constructor and SDK call parameter mapping in `py_agent_core/backends/azure_openai.py`.
- [x] 1.4 Update `OllamaBackend` constructor and SDK options dictionary wrapping in `py_agent_core/backends/ollama.py`.

## 2. Example Utilities & Verification

- [x] 2.1 Update `get_backend_from_args` in `examples/utils.py` to support parsing `--temperature` and `--top-p` and forwarding them to backends.
- [x] 2.2 Add unit tests to verify backend instantiations with custom `temperature` and `top_p`.
- [x] 2.3 Update documentation in `README.md` to show backend sampling options usage.
