"""Quality rules for production batches."""

from plant_ops.batches import Batch


def batches_with_invalid_run_hours(batches: list[Batch]) -> list[Batch]:
    """Return batches whose RunHours are not greater than 0 and at most 12."""
    return [batch for batch in batches if not 0 < batch.run_hours <= 12]
