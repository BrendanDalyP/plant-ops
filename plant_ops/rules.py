"""Quality rules a batch file must pass before its batches are loaded.

PURPOSE  One rule per thing that must be true of every batch. Each rule returns the batches
         that BREAK it, so an empty list means the rule passed and a failing rule shows the culprits.
"""

from __future__ import annotations

from collections import Counter

from plant_ops.batches import Batch


def check(
    batches: list[Batch], *, sku_ids: set[str], asset_plants: dict[str, str], loaded_ids: set[str]
) -> dict[str, list[Batch]]:
    """Run every rule on a batch file.

    PURPOSE     The gate: a file is loaded only when every list comes back empty.
    PSEUDOCODE  copies = how many times each BatchId appears in the file
                return {rule name: the batches that break it}, in the order of docs/rules.md
    """
    copies = Counter(b.batch_id for b in batches)
    return {
        "BatchId is present": [b for b in batches if not b.batch_id.strip()],
        "BatchId is unique in the file": [b for b in batches if copies[b.batch_id] > 1],  # every copy
        "Square feet are not negative": [
            b for b in batches if b.square_feet_produced < 0 or b.scrap_square_feet < 0
        ],
        "SkuId exists": [b for b in batches if b.sku_id not in sku_ids],
        # a machine that isn't in assets.csv has no plant, so it fails too
        "PlantId is the machine's plant": [b for b in batches if asset_plants.get(b.asset_id) != b.plant_id],
        "BatchId is not already loaded": [b for b in batches if b.batch_id in loaded_ids],
    }


def failing_ids(results: dict[str, list[Batch]]) -> set[str]:
    """The BatchId of every batch that broke at least one rule."""
    return {b.batch_id for broken in results.values() for b in broken}
