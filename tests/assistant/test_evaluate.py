"""Tests for the evaluation set and how it is scored.

PURPOSE  The evaluations judge the real model (Part 5). These tests judge the evaluations: every question says what
         a right answer contains, its numbers come from docs/assistant.md, and the scoring passes a right answer
         and fails a wrong one. ScriptedModel plays the model, so they run offline.
"""

import asyncio
import re
from pathlib import Path

SPEC = (Path(__file__).resolve().parents[2] / "docs" / "assistant.md").read_text(encoding="utf-8")
P01 = {"question": "What was P01's scrap rate in September 2026?", "expect": ["5.99"], "tools": ["scrap_rates"]}
CALL = ("scrap_rates", {"start": "2026-09-01", "end": "2026-09-30"})


def passes(evaluate, agent_module, model, item):
    results = asyncio.run(evaluate.score(agent_module.build_agent(client=model), [item]))
    return all(r.all_passed for r in results)


def test_every_question_says_what_a_right_answer_contains(evaluate):
    items = evaluate.load_questions()
    assert len(items) >= 8
    for item in items:
        assert item["question"].strip() and item["expect"], item


def test_expected_numbers_come_from_the_spec(evaluate):
    for item in evaluate.load_questions():
        for expected in item["expect"]:
            if re.search(r"\d", expected):
                assert expected in SPEC, f"{expected!r} isn't in docs/assistant.md: work it out there first"


def test_a_right_answer_passes(evaluate, agent_module, tools, scripted_model):
    model = scripted_model(CALL, "P01's scrap rate in September 2026 was 5.99%.")
    assert passes(evaluate, agent_module, model, P01)


def test_a_wrong_number_fails(evaluate, agent_module, tools, scripted_model):
    model = scripted_model(CALL, "P01's scrap rate in September 2026 was 6.10%.")
    assert not passes(evaluate, agent_module, model, P01)


def test_a_right_number_without_the_tool_fails(evaluate, agent_module, tools, scripted_model):
    model = scripted_model("P01's scrap rate in September 2026 was 5.99%.")
    assert not passes(evaluate, agent_module, model, P01)
