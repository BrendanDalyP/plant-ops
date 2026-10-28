# Measures

The definitions every report, query and agent uses. `Ops_Model` holds them as measures; anything that computes the same number elsewhere (a T-SQL view, a notebook) uses the same definition. A measure is a ratio of sums, never an average of batch rates.

| Measure | Table | Definition (DAX) | Folder | Format | Description |
| --- | --- | --- | --- | --- | --- |
| Scrap Rate % | fact_production | `DIVIDE ( [Scrap Square Feet], [Square Feet Produced] + [Scrap Square Feet] )` | Quality | 0.0% | Share of total board run that was scrapped: scrap square feet divided by good plus scrap square feet. A ratio of sums, never an average of batch rates. |
| Square Feet per Run Hour | fact_production | `DIVIDE ( [Square Feet Produced], SUM ( fact_production[RunHours] ) )` | Output | #,0.0 | Good board produced per hour of machine run time: total good square feet divided by total run hours. A ratio of sums, never an average of batch rates. |

`Scrap Rate %` comes from Session 1. `Square Feet per Run Hour` is added on Day 5.

## The same numbers in T-SQL

`sql/vw_scrap_rate_by_plant_month.sql` gives scrap rate per plant and month on the lakehouse's SQL analytics endpoint, with the definition above: `100.0 * SUM(ScrapSquareFeet) / (SUM(SquareFeetProduced) + SUM(ScrapSquareFeet))`, rounded to two places.

## Expected values

Worked out from the data pack's `fact_production` (64,368 batches, January 2024 to September 2026):

| Plant, period | Scrap Rate % | Square Feet per Run Hour |
| --- | --- | --- |
| P01, September 2026 | 5.65% (a DAX query returns 0.0565030; the 0.0% format shows 5.7%) | 63,396.4 |
| P01, all 33 months | 5.89% | 62,898.1 |

Name the month in every query: the lakehouse holds 33 months.

## MCP servers for DAX and T-SQL

The `fabric-skills` plugin brings these remote servers. If **MCP: List Servers** doesn't show them, add them with **MCP: Add Server** → **HTTP (HTTP or Server-Sent Events)**:

| Server ID | URL | What it does |
| --- | --- | --- |
| `powerbi-modeling-mcp` | `https://api.fabric.microsoft.com/v1/mcp/powerbi/authoring` | Reads and edits semantic models; runs DAX queries |
| `fabric-sqlendpoint` | `https://api.fabric.microsoft.com/v1/mcp/dataPlane/sqlEndpoint` | Runs T-SQL on a SQL analytics endpoint or warehouse (`execute_query`) |
