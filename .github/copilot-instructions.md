# Plant Ops

A small Python 3.11 app. It reads the plants' production batch files, checks them against quality rules, and serves statistics over a FastAPI web API. There is no database: `BatchStore` keeps batches in memory.

## Layout

- `plant_ops/batches.py`: the `Batch` dataclass and `read_batches()`, the only code that knows the CSV layout
- `plant_ops/rules.py`: the quality rules; `check()` returns {rule name: the batches that break it}
- `plant_ops/stats.py`: statistics for the managers' reports
- `plant_ops/api.py`: the web API, built by `create_app()`
- `data/`: test data. Never edit these files
- `docs/rules.md`: the rules in plain English, with their expected results
- `fabric/`: the items Fabric's Git integration writes from the Dev workspace (the gate notebook, the lakehouse,
  the semantic model). See `.github/instructions/fabric-*.instructions.md` before changing anything there
- `tests/fabric/`: the gate notebook's tests, run on local Spark; `docs/measures.md`: the model's definitions

## Commands

- `pytest -q` runs the tests and `ruff check .` the linter. Both pass before every commit.
- `uvicorn plant_ops.api:create_app --factory --reload` runs the API on port 8000.

## Conventions

- A rule returns the batches that break it, so an empty list means the rule passed.
- Expected numbers in tests come from `docs/rules.md` or are worked out by hand, never copied from the code's output.
- Every module has a PURPOSE line, and every function in `plant_ops/` with more than one line of logic has PURPOSE and PSEUDOCODE lines in its docstring.
- Standard library first. Add a package only when asked, pinned in `requirements-dev.txt`.
- Never change a test to make it pass. If a test looks wrong, say so and stop.
