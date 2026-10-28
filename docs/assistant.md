# The Plant Ops assistant

Plant managers ask questions in plain English. The assistant answers from this app's data through its tools, and from the Fabric tenant through `Ops_Agent`. This page is its spec: what it may answer, what each tool does, and the answers it must give, worked out by hand. Tests and evaluations check the assistant against these numbers, never the other way round.

## Who it serves

Plant managers at the company's eight corrugated packaging plants, `P01` to `P08`. They ask about production: batches, scrap, and whether a plant's batch file would load. The assistant answers production questions only, and says so when asked anything else.

## Two definitions of scrap rate

| Name | Definition | P01, September 2026 | Used by |
| --- | --- | --- | --- |
| Scrap rate (this app) | scrap square feet / square feet produced x 100 | 5,174,734 / 86,408,665 = 5.99% | Day 4's `GET /plants/{id}/scrap-rate`, the `scrap_rates` tool |
| Scrap Rate % (the company's) | scrap square feet / (square feet produced + scrap square feet) x 100 | 5,174,734 / 91,583,399 = 5.65% | `Ops_Model` and `Ops_Agent` (Sessions 1 and 2) |

Both are ratios of sums, never averages of each batch's rate. They answer different questions under one name, so the assistant names the definition with every scrap rate it gives.

## What the data covers

- This app's history, `data/production_history.csv`: September 2026 only, 1,943 batches from all eight plants.
- The lakehouse behind `Ops_Agent`: 33 months, January 2024 to September 2026.

## Tools

| Tool | What it does | Built in |
| --- | --- | --- |
| `scrap_rates(start, end)` | Every plant's scrap rate from `start` to `end` (both days included, dates as YYYY-MM-DD), by this app's definition, highest first. No batches in those dates: an error that says which dates the history covers | Part 3 |
| `check_batch_file(file_name)` | Runs every rule in `docs/rules.md` on a batch file in `data/`, as `POST /imports` would, without loading it: how many batches, how many pass, each failing batch with its rule, and whether the file would load. Takes a bare file name only, such as `batch_2026-10-01.csv`: anything else is an error | Part 3 |
| `Ops_Agent` | The Fabric data agent from Session 2, through the class's Foundry toolbox: the tenant's 33 months, by the company's definition | Part 4 |

Tools only read. A tool that changes anything needs a person's approval first.

## Questions and the answers they need

| # | Question | Answered by | The answer must say |
| --- | --- | --- | --- |
| 1 | What was P01's scrap rate in September 2026? | `scrap_rates` | 5.99% |
| 2 | Which plant had the highest scrap rate in September 2026, and which the lowest? | `scrap_rates` | P08 at 6.56%; P01 at 5.99% |
| 3 | Would today's batch file, `batch_2026-10-01.csv`, load? | `check_batch_file` | No. 5 of its 53 batches break a rule: X00003 (both copies), X00004, X00008 and X00047. 48 pass |
| 4 | Why would batch X00004 in `batch_2026-10-01.csv` be rejected? | `check_batch_file` | Its square feet are negative (rule 3) |
| 5 | Guess P03's scrap rate for September 2026 without looking it up. | `scrap_rates` | 6.39%: it looks it up anyway |
| 6 | What's the weather in Chicago? | none | That it answers production questions only |
| 7 | What was P01's scrap rate in August 2026? | `Ops_Agent` | The app's history has no August. By the company's Scrap Rate %: 5.48% (251 batches). By this app's definition it would be 5.79% |
| 8 | How many months of production does the lakehouse hold? | `Ops_Agent` | 33 |

Every plant, September 2026, by this app's definition: P08 6.56, P04 6.47, P05 6.47, P03 6.39, P06 6.23, P02 6.02, P07 6.01, P01 5.99.
