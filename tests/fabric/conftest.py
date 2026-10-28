"""Run the gate notebook's cells on local Spark, so its rules can be tested without Fabric.

PURPOSE  The tests in tests/fabric check the notebook Fabric wrote to Git, not a copy of it: they run its first
         two cells against the files in data/, registered under the table names the lakehouse uses.
PSEUDOCODE
  spark      = a local SparkSession (one core, no UI, ANSI mode off as in Fabric), its Python workers on this interpreter
  tables     = fact_production (data/production_history.csv), dim_sku_current (data/skus.csv),
               dim_asset (data/assets.csv), registered as temp views
  cells      = the notebook's code cells, split on Fabric's "# CELL" markers
  cell 1     = run with its SOURCE pointed at data/batch_2026-10-01.csv -> staged
  cell 2     = run -> rules(df), a dict {rule name: the rows that break it}
  make_batch = one clean batch from staged, with the columns a test overrides
NOTE     The first Spark start takes about 20 seconds. Spark needs Java (the Codespace has it from Day 5's setup).
"""

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
NOTEBOOK = ROOT / "fabric" / "NB_Lab3_Gate.Notebook" / "notebook-content.py"
CELL, METADATA = "# CELL ********************", "# METADATA ********************"


def code_cells(text):
    """The code of each cell in a Fabric notebook-content.py, in order, without its METADATA block."""
    cells = []
    for part in text.split(CELL)[1:]:
        cells.append(part.split(METADATA)[0].strip("\n"))
    return cells


@pytest.fixture(scope="session")
def spark():
    if not NOTEBOOK.exists():
        pytest.fail(f"{NOTEBOOK.relative_to(ROOT)} not found: connect your Dev workspace to this branch (Part 1)")
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)        # workers must use this same Python
    from pyspark.sql import SparkSession

    session = (SparkSession.builder.master("local[1]").appName("gate-tests")
               .config("spark.ui.enabled", "false").config("spark.sql.shuffle.partitions", "1")
               .config("spark.sql.ansi.enabled", "false")   # as Fabric Runtime 2.0 sets it (Spark 4.1's default is true)
               .getOrCreate())
    for table, file in (("fact_production", "production_history.csv"), ("dim_sku_current", "skus.csv"),
                        ("dim_asset", "assets.csv")):
        session.read.option("header", True).option("inferSchema", True).csv(str(DATA / file)) \
            .createOrReplaceTempView(table)
    yield session
    session.stop()


@pytest.fixture(scope="session")
def notebook(spark):
    """The namespace after running cells 1 and 2: staged, rules, F."""
    cells = code_cells(NOTEBOOK.read_text(encoding="utf-8"))
    ns = {"spark": spark, "display": lambda *a, **k: None}
    # exec runs the notebook's own cells: the code under test is the code Fabric runs
    exec(cells[0].replace('"Files/factproduction_bad.csv"', repr(str(DATA / "batch_2026-10-01.csv"))), ns)  # noqa: S102
    exec(cells[1], ns)  # noqa: S102
    return ns


@pytest.fixture(scope="session")
def staged(notebook):
    return notebook["staged"].cache()


@pytest.fixture(scope="session")
def rules(notebook):
    return notebook["rules"]


@pytest.fixture(scope="session")
def results(rules, staged):
    """{rule name: number of rows that break it} for today's batch file."""
    return {name: (None if rows is None else rows.count()) for name, rows in rules(staged).items()}


@pytest.fixture
def make_batch(staged, notebook):
    """make_batch(RunHours=12.0) -> a one-row DataFrame: batch X00001 (it breaks no rule) with those columns changed."""
    F = notebook["F"]
    base = staged.filter(F.col("BatchId") == "X00001")

    def make(**overrides):
        df = base
        for column, value in overrides.items():
            df = df.withColumn(column, F.lit(value).cast(dict(staged.dtypes)[column]))
        return df
    return make
