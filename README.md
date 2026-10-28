# Plant Ops

A small practice app for the GitHub Copilot build-along (Fabric AI Enablement, Session 4): it reads the plants' production batch files, checks them against quality rules, and answers questions over a web API. You build the missing parts with Copilot during the day.

## Start here

1. Work in your own copy. If you're looking at the course template, `plant-ops`, make one first: **Use this template** → **Create a new repository** → **Owner**: the course organization, **Repository name**: `plant-ops-<initials>`, **Private**, select **Include all branches** → **Create repository from template**. Your instructor may have made it for you already.
2. In your copy: **Code** → **Codespaces** → **Create codespace on main**. Python, the packages, Spec Kit, Copilot CLI and the extensions are installed for you; the first start takes a few minutes.
3. In the terminal: `git switch -c work`
4. Follow the build-along guide your instructor gave you, from Part 1.

The CI check fails on `main` at the start. That's expected: the tests fail on purpose until you fix the code in Parts 2 and 3.

## What's in it

| Path | What it is |
| --- | --- |
| `plant_ops/batches.py` | A production batch, and reading a batch file (you write the reader in Part 2) |
| `plant_ops/stats.py` | Scrap rate per plant (it has bugs; Part 3) |
| `plant_ops/rules.py` | The quality rules (built in Part 4) |
| `plant_ops/store.py`, `reference_data.py` | The loaded batches, the SKU list and the machine list |
| `plant_ops/api.py` | The web API. Run it with `uvicorn plant_ops.api:create_app --factory --reload` |
| `data/` | The September history, one day's batch file with problems in it, the SKU and machine lists |
| `docs/rules.md` | The rules in plain English, with the expected results |
| `docs/copilot-gotchas.md` | Your log of what Copilot got wrong |
| `cheat-sheet.md` | Yours to fill in during the day |

## Commands

    pytest -q        # the tests (some fail on purpose at the start)
    ruff check .     # the linter

## Behind? Jump to a checkpoint

Each part ends at a checkpoint branch. To pick up from one, run this on your own branch (`work`, or `spec` in Part 7). It replaces every file except your cheat sheet and gotchas log with the checkpoint's, as one new commit, so your branch's pull request into `main` still works:

    git fetch
    git restore --source origin/checkpoint/04 --staged --worktree -- . ':!cheat-sheet.md' ':!docs/copilot-gotchas.md'
    git commit -m "Catch up to checkpoint 04"
    git push -u origin HEAD

Don't open a pull request from a checkpoint branch itself: in a repo made from a template, each branch has its own unrelated history.
