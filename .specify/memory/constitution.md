# Plant Ops Constitution

## Core Principles

### I. A batch file is loaded whole or not at all

Every rule in `docs/rules.md` runs on every batch file. If any batch breaks any rule, nothing from that file is loaded, and the answer names each failing batch and the rule it broke.

### II. Expected results come first (NON-NEGOTIABLE)

Tests take their expected numbers from `docs/rules.md`, or from working them out by hand before the code exists. A test is never changed to make code pass.

### III. Small and standard

Python 3.11, the standard library, and FastAPI for HTTP. A new package needs a reason in the plan and a pinned version in `requirements-dev.txt`.

### IV. One place for each concern

Only `plant_ops/batches.py` knows the CSV layout. Only `plant_ops/rules.py` decides what is valid. `plant_ops/api.py` translates between HTTP and those modules and holds no rules of its own.

### V. Readable by both teams

Every module has a PURPOSE line, and every function in `plant_ops/` with more than one line of logic has PURPOSE and PSEUDOCODE lines in its docstring, so a data engineer and an app developer can both review it.

## Quality Gates

`ruff check .` and `pytest -q` pass before every commit, and in CI on every pull request. Every pull request gets a review from a person; Copilot's review is a second opinion, not the approval.

## Governance

This constitution overrides other practices in the repo. Changing it takes a pull request, a review, and a new version number.

**Version**: 1.0.0 | **Ratified**: 2026-10-28 | **Last Amended**: 2026-10-28
