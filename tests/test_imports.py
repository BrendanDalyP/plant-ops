"""Tests for POST /imports: a batch file is loaded whole, or not at all.

PURPOSE  The acceptance scenarios from specs/001-batch-import/spec.md, run against the app.
         The expected numbers come from docs/rules.md.
"""

import pytest
from fastapi.testclient import TestClient

from plant_ops.api import create_app
from plant_ops.reference_data import DATA

BATCH_FILE = DATA / "batch_2026-10-01.csv"
BROKEN_IDS = {"X00003", "X00004", "X00008", "X00047"}  # read from the file: the 5 rows docs/rules.md counts


@pytest.fixture
def client():
    return TestClient(create_app())


def upload(client, content: bytes):
    return client.post("/imports", files={"file": ("batch.csv", content, "text/csv")})


def clean_file() -> bytes:
    """The batch file without the batches that break a rule: 48 batches."""
    lines = BATCH_FILE.read_text(encoding="utf-8").splitlines()
    kept = [lines[0]] + [line for line in lines[1:] if line.split(",")[0] not in BROKEN_IDS]
    return ("\n".join(kept) + "\n").encode("utf-8")


def loaded(client) -> int:
    return client.get("/health").json()["batches"]


def test_a_file_that_breaks_rules_is_rejected_whole(client):
    response = upload(client, BATCH_FILE.read_bytes())
    assert response.status_code == 422
    assert len(response.json()["failures"]) == 5
    assert loaded(client) == 1943


def test_each_failure_names_the_batch_and_the_rule(client):
    failures = upload(client, BATCH_FILE.read_bytes()).json()["failures"]
    assert {"batch_id": "X00004", "rule": "Square feet are not negative"} in failures


def test_a_clean_file_is_loaded(client):
    response = upload(client, clean_file())
    assert response.status_code == 201
    assert response.json() == {"accepted": 48}
    assert loaded(client) == 1943 + 48


def test_the_same_file_twice_is_rejected_the_second_time(client):
    upload(client, clean_file())
    response = upload(client, clean_file())
    assert response.status_code == 422
    failures = response.json()["failures"]
    assert len(failures) == 48
    assert {f["rule"] for f in failures} == {"BatchId is not already loaded"}
    assert loaded(client) == 1943 + 48


def test_an_unreadable_file_is_400(client):
    assert upload(client, b"not,a,batch,file\n1,2,3,4\n").status_code == 400


def test_a_file_with_no_batches_is_400(client):
    header = BATCH_FILE.read_text(encoding="utf-8").splitlines()[0]
    assert upload(client, (header + "\n").encode("utf-8")).status_code == 400
