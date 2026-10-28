# Agent rules

Two kinds of agent work on this repo: Copilot, which changes the code, and the Plant Ops assistant, which runs in Foundry and answers plant managers. This page says what each may do. Written on Day 5 by you and your partner; both of you review changes to it.

## Copilot may change, in a pull request

- App code and its tests in `plant_ops/` and `tests/`, through the skills and instructions in `.github/`.
- The assistant's tools in `assistant/tools.py`, each with its tests, a row in `docs/assistant.md` and a question in `evals/questions.yaml`.

## Copilot may not change

- `.github/workflows/`, `deploy/`, `main.py`, `requirements.txt` and `assistant/agent.py` (its instructions are the assistant's prompt) without the other of us approving: `CODEOWNERS` and the ruleset require a code owner's approval, and nobody approves their own pull request.
- `evals/questions.yaml`'s expected answers, unless `docs/assistant.md` changed first: a test is never changed to make it pass.
- Anything in the Foundry project directly: model deployments, the toolbox, its connections, other people's agents.

## What the assistant may do

- Read only. Its tools read this app's data and ask `Ops_Agent`; none of them changes anything.
- A tool that would change something (hold a batch file, say) waits for a person to approve each call (`approval_mode="always_require"`), and arrives through a reviewed pull request.
- It answers production questions only, from its tools, naming the source and the definition of every scrap rate.

## MCP servers and toolboxes we allow, and how

- `azure` (the Azure MCP Server, from the `azure` plugin): read tools only in the chat; we refuse anything that creates, changes or deletes a resource.
- The class toolbox (`TOOLBOX_ENDPOINT`): the assistant's way to `Ops_Agent`, which only answers questions.
- **Manual** permissions in the chat, always. Every call that writes is read before it is approved.

## Who reviews an agent's pull request

- The person who assigned the task reads the session log and the diff, and runs the tests and the evaluations; the partner approves.

## What must pass before a merge, and before a deployment

- `ruff check .` and `pytest -q` in CI, with no test calling Foundry.
- `python -m assistant.evaluate` with every question passing, run by the person who deploys, before `deploy_agent.py`.

## What stays with people

- Deploying the hosted agent, and choosing which version gets the traffic.
- The instructions, and what the assistant may answer.
- Who can call the hosted agent, and with which role.
