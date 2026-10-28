-- =====================================================================================
-- vw_scrap_rate_by_plant_month · Scrap rate per plant and month, on Ops_Lakehouse's SQL analytics endpoint
-- PURPOSE  The same number Ops_Model's Scrap Rate % gives, for people and tools that use T-SQL: one
--          definition (docs/measures.md), whatever the language.
-- PSEUDOCODE
--   group fact_production by plant, year and month
--   scrap rate = 100 x total scrap / (total good + total scrap), rounded to 2 places: a ratio of sums
-- NOTE     A lakehouse's SQL analytics endpoint takes views but no table changes. Run this once per workspace;
--          to change the view, DROP VIEW it first.
-- =====================================================================================
CREATE VIEW dbo.vw_scrap_rate_by_plant_month AS
SELECT
    PlantId,
    YEAR(ShiftDate)  AS ShiftYear,
    MONTH(ShiftDate) AS ShiftMonth,
    COUNT(*)         AS Batches,
    ROUND(100.0 * SUM(CAST(ScrapSquareFeet AS float))          -- float first: whole-number division gives 0 or 5
          / (SUM(CAST(SquareFeetProduced AS float)) + SUM(CAST(ScrapSquareFeet AS float))), 2) AS ScrapRatePct
FROM dbo.fact_production
GROUP BY PlantId, YEAR(ShiftDate), MONTH(ShiftDate);
