# Agent rules

What Copilot and other agents may do in this repo. Written on Day 5 by you and your partner; both of you review changes to it.

## Agents may change, in a pull request

- App code and its tests in `plant_ops/` and `tests/`, through the skills and instructions in `.github/`.
- Rules in the gate notebook's `rules()` cell and their tests, through the `new-rule` skill.
- Measures in `fabric/Ops_Model.SemanticModel/`, as `docs/measures.md` defines them.
- SQL files in `sql/`.

## Agents may not change

- `.github/workflows/`, `deploy/`, `fabric/parameter.yml` and this file without the other of us approving: `CODEOWNERS` and the ruleset require a code owner's approval, and nobody approves their own pull request.
- `.platform` files, `# META` lines, `lineageTag` lines and item folder names under `fabric/`.
- Anything in a workspace directly: Fabric items change through Git and **Update all**, never through an MCP tool that writes.
- OneLake roles, RLS roles, workspace access and `Ops_Agent`'s instructions: a person changes these in Fabric.

## MCP servers we allow, and how

- `fabric` (the Fabric MCP Server, in `.mcp.json`): read tools only; we refuse its create, update and delete tools.
- `ops-agent` (`Ops_Agent`'s endpoint, in each person's user configuration): questions only.
- `powerbi-modeling-mcp` and `fabric-sqlendpoint` (from the `fabric-skills` plugin): DAX and T-SQL queries on the Dev workspace; the one T-SQL change allowed is a view from a file in `sql/`.
- `FabricIQ` (also from the plugin): not used; we leave it stopped.
- **Manual** permissions, always. Every call that writes is read before it is approved.

## Who reviews an agent's pull request

- The person who assigned the task reads the session log and the diff, and runs the `reviewer` agent; the partner approves.

## What CI must pass before a merge

- `ruff check .` and `pytest -q`, including the gate notebook's tests on local Spark and `test_parameter_yml.py`.

## What stays with people

- Approving every deployment to Test.
- Session 3's agent checks on `Ops_Agent`: a service principal can't call a data agent with a KQL source, so CI can't run them.
- Anything that changes who can see what.
