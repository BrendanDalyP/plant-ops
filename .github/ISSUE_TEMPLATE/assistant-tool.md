---
name: Assistant tool
about: One new read-only tool for the Plant Ops assistant, sized for Copilot cloud agent
title: "Tool: square feet per run hour"
labels: []
---

## Outcome

Plant managers can ask the assistant how much board each plant runs per hour of machine time, for any dates the history covers.

## Definition

Square feet per run hour = total square feet produced / total run hours, a ratio of sums over the batches from `start` to `end` (both days included), rounded to 1 decimal place. The data team's `Square Feet per Run Hour` measure in `Ops_Model` uses the same definition, so the two must agree.

Worked out by hand for September 2026: P01 86,408,665 square feet in 1,362.99 run hours = 63,396.4; P02 36,934.8; P08 69,848.8, the highest.

## Acceptance tests

- [ ] `square_feet_per_run_hour_by_plant(batches, start, end)` in `plant_ops/stats.py`, built like `scrap_rate_by_plant`, with tests in `tests/test_stats.py`.
- [ ] A tool `square_feet_per_run_hour(start, end)` in `assistant/tools.py` that wraps it, built like `scrap_rates`: every plant, highest first, a description and parameter descriptions written for the model, and the definition in its description.
- [ ] For `2026-09-01` to `2026-09-30` it gives P01 63396.4 and P02 36934.8, with P08 first at 69848.8.
- [ ] Dates with no batches, or a date that isn't YYYY-MM-DD, give an `error`, as `scrap_rates` does.
- [ ] The model is offered the tool: a test in `tests/assistant/test_agent.py` with `scripted_model`.
- [ ] `docs/assistant.md` lists the tool, with a question and P01's number; `evals/questions.yaml` has that question.
- [ ] `pytest -q` and `ruff check .` pass, and no test calls Foundry.

## Files to touch

- `plant_ops/stats.py`
- `tests/test_stats.py`
- `assistant/tools.py`
- `tests/assistant/test_tools.py`
- `tests/assistant/test_agent.py`
- `docs/assistant.md`
- `evals/questions.yaml`

## How to verify

`pytest -q`

## Out of scope

Any other tool, the agent's instructions, `deploy/`, `main.py`, the rest of `plant_ops/`, `.github/`.
