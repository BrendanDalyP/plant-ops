"""The batches already loaded.

PURPOSE  An in-memory stand-in for the production database: the history, plus anything
         imported while the app runs. Restarting the app starts again from the history file.
"""

from __future__ import annotations

from pathlib import Path

from plant_ops.batches import Batch, read_batches


class BatchStore:
    """Holds loaded batches in memory."""

    def __init__(self, batches: list[Batch]) -> None:
        self._batches = list(batches)

    @classmethod
    def from_csv(cls, path: str | Path) -> BatchStore:
        """A store holding every batch in a CSV file."""
        return cls(read_batches(path))

    def all(self) -> list[Batch]:
        """Every loaded batch, oldest first."""
        return list(self._batches)

    def batch_ids(self) -> set[str]:
        """The BatchId of every loaded batch."""
        return {b.batch_id for b in self._batches}

    def add(self, batches: list[Batch]) -> None:
        """Load more batches. The caller checks them first."""
        self._batches.extend(batches)
