# Batch file rules

Every batch in a file must pass every rule before any batch from that file is loaded. A rule *fails* on the batches that break it.

| # | Rule | A batch breaks it when | Batches that break it in `data/batch_2026-10-01.csv` |
| --- | --- | --- | --- |
| 1 | BatchId is present | its BatchId is empty | 0 |
| 2 | BatchId is unique in the file | its BatchId appears more than once in the file (every copy breaks it) | 2 |
| 3 | Square feet are not negative | SquareFeetProduced or ScrapSquareFeet is below 0 | 1 |
| 4 | SkuId exists | its SkuId isn't in `data/skus.csv` | 1 |
| 5 | PlantId is the machine's plant | its AssetId isn't in `data/assets.csv`, or the machine stands in another plant | 1 |
| 6 | BatchId is not already loaded | its BatchId is already in the store (the history) | 0 |
| 7 | Scrap is not more than produced | ScrapSquareFeet is greater than SquareFeetProduced | 0 |
| 8 | RunHours is greater than 0 and at most 12 | RunHours is 0 or less, or more than 12 | 0 |
| 9 | Shift is one of the values already in gold | its Shift isn't one gold already has (A, B or C); checked in the gate notebook only | 0 |

48 of the file's 53 batches break no rule.

The counts were worked out by hand from the file. Tests check the code against these numbers, never the other way round.
