# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "1b2c3d4e-5f60-4718-8a9b-0c1d2e3f4a5b",
# META       "default_lakehouse_name": "Ops_Lakehouse",
# META       "default_lakehouse_workspace_id": "aa11bb22-cc33-4d44-8e55-ff6677889900",
# META       "known_lakehouses": [
# META         {
# META           "id": "1b2c3d4e-5f60-4718-8a9b-0c1d2e3f4a5b"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# =====================================================================================
# CELL 1 of 6 · NB_Lab3_Gate · B3 · Stage today's batch file
# PURPOSE  Read the file and give every column the type gold stores it as. Nothing is written yet.
# PSEUDOCODE
#   staged = the CSV, with dates as dates, the shift start as a timestamp and numbers as numbers
#   show a few rows and how many batches arrived
# =====================================================================================
from pyspark.sql import functions as F       # F = Spark's column functions (col, to_date, lit, ...)

SOURCE = "Files/factproduction_bad.csv"
staged = (spark.read.option("header", True).csv(SOURCE)
          .select("BatchId", "PlantId", "AssetId", "SkuId",
                  F.to_date("ShiftDate").alias("ShiftDate"),
                  F.to_timestamp("ShiftStart").alias("ShiftStart"), "Shift",
                  F.col("RunHours").cast("double").alias("RunHours"),
                  F.col("SquareFeetProduced").cast("bigint").alias("SquareFeetProduced"),
                  F.col("ScrapSquareFeet").cast("bigint").alias("ScrapSquareFeet")))
display(staged.limit(5))
print("staged:", staged.count(), "batches")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================================
# CELL 2 of 6 · NB_Lab3_Gate · B3 · The quality rules
# PURPOSE  One rule per thing that must be true before a batch reaches gold. Each rule is the rows
#          that BREAK it, so a passing rule is an empty DataFrame and a failing one shows the culprits.
# PSEUDOCODE
#   gold, sku, asset = the tables the rules compare against; dup_ids = BatchIds sent more than once
#   return {rule name: the rows of df that break it}   (None = not written yet: the gate fails it)
# =====================================================================================
def rules(df):
    gold = spark.table("fact_production")                 # what is already loaded
    sku = spark.table("dim_sku_current")                  # every SKU the company makes today
    asset = spark.table("dim_asset")                      # every machine, with the plant it is in
    dup_ids = df.groupBy("BatchId").count().filter("count > 1").select("BatchId")   # sent twice
    return {
        # 1. rows with no BatchId at all
        "BatchId is present": df.filter(F.col("BatchId").isNull()),
        # 2. every copy of a BatchId sent more than once, not just the extra one
        "BatchId is unique in the file": df.join(dup_ids, "BatchId"),
        # 3. negative square feet are a keying error
        "Square feet are not negative": df.filter("SquareFeetProduced < 0 OR ScrapSquareFeet < 0"),
        # 4. rows whose SKU has NO match in today's SKU list
        "SkuId exists": df.join(sku, "SkuId", "left_anti"),
        # 5. rows with no machine, or whose machine stands in another plant
        "PlantId is the machine's plant": (df.join(asset.select("AssetId", F.col("PlantId").alias("MachinePlant")),
                                                   "AssetId", "left")
                                             .filter("MachinePlant IS NULL OR MachinePlant <> PlantId")),
        # 6. rows already in gold: loading them again would count them twice
        "BatchId is not already loaded": df.join(gold.select("BatchId"), "BatchId", "left_semi"),
        # 7. a batch can't scrap more board than it made
        "Scrap is not more than produced": df.filter("ScrapSquareFeet > SquareFeetProduced"),
        # 8. a batch that ran ran for some time, and a shift is at most 12 hours (a missing value fails too)
        "RunHours is greater than 0 and at most 12": df.filter("RunHours IS NULL OR RunHours <= 0 OR RunHours > 12"),
    }
print("rules defined:", [name for name, rows in rules(staged).items() if rows is not None])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================================
# CELL 3 of 6 · NB_Lab3_Gate · B3 · The gate and the load (plumbing)
# PURPOSE  gate(df) runs every rule and reports each one; load_to_gold(df) refuses to write anything
#          unless every rule passes, then appends the rows with the SKU version in force that day.
# PSEUDOCODE
#   gate(df): for each rule: None -> NOT WRITTEN (counts as a failure); else count its rows;
#             print OK or FAIL (n rows); return the number of failing rules and the rules
#   load_to_gold(df): if the gate fails -> raise QualityGate, write nothing
#                     else INSERT the rows into fact_production, each with the SkuKey whose
#                     ValidFrom..ValidTo covers its ShiftDate (Session 1's SCD2 join),
#                     and check that exactly that many rows arrived
# =====================================================================================
class QualityGate(Exception):
    """Raised when data breaks a rule. In a pipeline it fails the notebook activity."""

def gate(df):
    checked, failed = rules(df), 0
    for name, rows in checked.items():
        n = None if rows is None else rows.count()          # runs the rule against the data
        failed += n != 0                                     # None (not written) or rows -> a failure
        print(f"{name:44} {'NOT WRITTEN' if n is None else 'OK' if n == 0 else f'FAIL ({n} rows)'}")
    return failed, checked

def load_to_gold(df):
    failed, _ = gate(df)
    if failed:
        raise QualityGate(f"{failed} rule(s) failed: gold load stopped, nothing written")
    n, before = df.count(), spark.table("fact_production").count()
    df.createOrReplaceTempView("incoming")                  # lets the SQL below call df "incoming"
    spark.sql("""
        INSERT INTO fact_production                         -- columns in the table's own order
        SELECT i.BatchId, i.PlantId, i.AssetId, i.SkuId, s.SkuKey,
               i.ShiftDate, i.ShiftStart, i.Shift, i.RunHours,
               i.SquareFeetProduced, i.ScrapSquareFeet
        FROM incoming i
        JOIN dim_sku s ON i.SkuId = s.SkuId AND i.ShiftDate BETWEEN s.ValidFrom AND s.ValidTo""")
    added = spark.table("fact_production").count() - before
    assert added == n, f"{n} passed the gate but {added} arrived: a SKU version is missing"   # inner JOIN drops silently
    print(f"gold load complete: {n} batches appended")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================================
# CELL 4 of 6 · NB_Lab3_Gate · B3 · Try to load the raw file
# PURPOSE  Send the batch through the gate exactly as it arrived.
# PSEUDOCODE
#   load_to_gold(staged): run every rule; any failure raises QualityGate before anything is written
# NOTE     Expect rules to fail and the cell to turn red. A red cell here is the gate working.
# =====================================================================================
load_to_gold(staged)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================================
# CELL 5 of 6 · NB_Lab3_Gate · B3 · Quarantine the bad rows, load the rest through the same gate
# PURPOSE  Keep the bad rows somewhere someone owns, with the rule each one broke, and let the good
#          rows through: the same gate decides, so nothing skips the checks.
# PSEUDOCODE
#   run the rules; for each failing rule except "already loaded" (that one is about gold, not the
#       data): tag its rows with the rule's name; stack them into one quarantine set
#   save it as quarantine_production (someone has to fix these)
#   clean = staged rows whose BatchId is not in quarantine; load_to_gold(clean)
# =====================================================================================
_, checked = gate(staged)
quarantine = None
for name, rows in checked.items():
    if name == "BatchId is not already loaded" or rows is None:
        continue
    tagged = rows.select(*staged.columns).withColumn("FailedRule", F.lit(name))   # lit = same value on every row
    quarantine = tagged if quarantine is None else quarantine.unionByName(tagged)
quarantine.write.mode("overwrite").format("delta").saveAsTable("quarantine_production")

bad_ids = spark.table("quarantine_production").select("BatchId").distinct()     # read the SAVED table
clean = staged.join(bad_ids, "BatchId", "left_anti")                           # staged rows NOT quarantined
print("quarantined rows:", spark.table("quarantine_production").count(), "| clean batches:", clean.count())
load_to_gold(clean)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# =====================================================================================
# CELL 6 of 6 · NB_Lab3_Gate · B3 · Load the same clean rows again, as a scheduler might on a retry
# PURPOSE  Prove the load is safe to re-run.
# PSEUDOCODE
#   load_to_gold(clean) a second time: "BatchId is not already loaded" should catch every row
# NOTE     That rule is what makes the notebook safe to re-run: nothing is ever written twice.
# =====================================================================================
load_to_gold(clean)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
