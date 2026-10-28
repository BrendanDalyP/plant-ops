---
applyTo: "assistant/**,main.py,deploy/deploy_agent.py,tests/assistant/**"
---

# The Plant Ops assistant

- Microsoft Agent Framework for Python, pinned in `requirements-dev.txt` (agent-framework-core 1.24.0, agent-framework-foundry 1.16.0). Use today's names: `Agent` and `tool` from `agent_framework`; `FoundryChatClient` and `FoundryToolbox` from `agent_framework.foundry`; `ResponsesHostServer` from `agent_framework_foundry_hosting`. `ChatAgent`, `ai_function`, `AzureAIAgentClient` and `AzureOpenAIChatClient` are older names: don't use them.
- Sign in with `DefaultAzureCredential()`. Never an API key, and never a secret in code, a test or a commit.
- Settings come from the environment: `FOUNDRY_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`, `TOOLBOX_ENDPOINT`, `PLANT_OPS_AGENT_NAME`. Only entry points (`python -m assistant`, `main.py`, the evaluations, the deployment) load `.env`; `build_agent()` never does.
- `build_agent()` in `assistant/agent.py` is the only place the agent is built. Everything else calls it.
- A tool wraps code from `plant_ops/`; it never computes a number itself. It returns a dict. Bad input returns a dict with an `error` key that tells the model what to ask for, never an exception.
- The model reads a tool's name, its `description=` and its parameter descriptions (`Annotated[str, Field(description=...)]`), so write those for the model, with units and definitions. PURPOSE and PSEUDOCODE stay in the docstring, for people.
- Tools only read. A tool that changes anything uses `approval_mode="always_require"`.
- Tests never call Foundry: they pass `scripted_model(...)` from `tests/assistant/conftest.py` as the client. Expected numbers come from `docs/assistant.md`.
