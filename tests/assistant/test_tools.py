"""Tests for the assistant's tools.

PURPOSE  Each tool must give the numbers in docs/assistant.md, worked out by hand, and must refuse input that could
         reach outside data/: a tool's arguments come from the model, so treat them like any user input.
"""

import pytest


def rates(result):
    return {r["plant_id"]: r["scrap_rate_pct"] for r in result["rates"]}


def test_p01_september_scrap_rate(tools):
    assert rates(tools.scrap_rates("2026-09-01", "2026-09-30"))["P01"] == 5.99


def test_scrap_rates_highest_first(tools):
    result = tools.scrap_rates("2026-09-01", "2026-09-30")["rates"]
    assert [r["plant_id"] for r in result] == ["P08", "P04", "P05", "P03", "P06", "P02", "P07", "P01"]
    assert (result[0]["scrap_rate_pct"], result[-1]["scrap_rate_pct"]) == (6.56, 5.99)


def test_scrap_rates_with_no_batches_says_what_the_history_covers(tools):
    result = tools.scrap_rates("2026-08-01", "2026-08-31")
    assert "rates" not in result
    assert "2026-09-01" in result["error"] and "2026-09-30" in result["error"]


@pytest.mark.parametrize("start", ["2026-13-01", "September", ""])
def test_scrap_rates_with_a_bad_date_asks_for_yyyy_mm_dd(tools, start):
    assert "YYYY-MM-DD" in tools.scrap_rates(start, "2026-09-30")["error"]


def test_todays_file_would_not_load(tools):
    result = tools.check_batch_file("batch_2026-10-01.csv")
    assert (result["batches"], result["pass"], result["would_load"]) == (53, 48, False)
    assert sorted(f["batch_id"] for f in result["failures"]) == ["X00003", "X00003", "X00004", "X00008", "X00047"]


def test_check_batch_file_names_the_rule(tools):
    failures = tools.check_batch_file("batch_2026-10-01.csv")["failures"]
    assert {f["rule"] for f in failures if f["batch_id"] == "X00004"} == {"Square feet are not negative"}


@pytest.mark.parametrize("name", ["../pyproject.toml", "/etc/passwd", "data/batch_2026-10-01.csv",
                                  "missing.csv", "skus.csv"])
def test_check_batch_file_refuses_anything_but_a_batch_file_in_data(tools, name):
    result = tools.check_batch_file(name)
    assert set(result) == {"error"}


def test_every_tool_is_described_for_the_model(tools):
    for t in (tools.scrap_rates, tools.check_batch_file):
        assert t.description and "PSEUDOCODE" not in t.description      # the model reads this; people read the docstring
        for name, schema in t.parameters()["properties"].items():
            assert schema.get("description"), f"{t.name}({name}) has no description for the model"
