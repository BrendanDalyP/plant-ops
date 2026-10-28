"""Reference data the quality rules compare against.

PURPOSE  Load the SKU list and the machine list once, in the shapes the rules need.
"""

from __future__ import annotations

import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def load_sku_ids(path: str | Path = DATA / "skus.csv") -> set[str]:
    """Every SKU the company makes today.

    PURPOSE     Rule 4 checks each batch's SkuId against this set.
    PSEUDOCODE  read skus.csv; return the set of its SkuId values
    """
    with open(path, newline="", encoding="utf-8") as f:
        return {row["SkuId"] for row in csv.DictReader(f)}


def load_asset_plants(path: str | Path = DATA / "assets.csv") -> dict[str, str]:
    """Every machine and the plant it stands in.

    PURPOSE     Rule 5 checks each batch's PlantId against its machine's plant.
    PSEUDOCODE  read assets.csv; return {AssetId: PlantId}
    """
    with open(path, newline="", encoding="utf-8") as f:
        return {row["AssetId"]: row["PlantId"] for row in csv.DictReader(f)}
