---
description: Writing code in the Fabric notebooks stored under fabric/
applyTo: "fabric/**/notebook-content.py"
---
- The notebook runs on Fabric Runtime 2.0 (Spark 4.1, Python 3.13). `spark`, `display` and `notebookutils` already exist; don't create a SparkSession.
- Tables in the default lakehouse are read by name (`spark.table("fact_production")`), files by relative path (`Files/...`).
- A rule in the `rules()` cell returns the rows that break it, under the same name as in `docs/rules.md`. Write it with Spark column expressions, never with Python loops over rows or `collect()`.
- Fabric Runtime 2.0 turns ANSI mode off (`spark.sql.ansi.enabled` is false, unlike Spark 4.1's default), so a bad cast gives NULL instead of failing: cast strings explicitly and handle NULLs on purpose. The local tests run Spark the same way.
- Every cell opens with the house header: PURPOSE, PSEUDOCODE, then comments on the calls that matter.
- Test a change with `pytest -q tests/fabric` before you commit it.
