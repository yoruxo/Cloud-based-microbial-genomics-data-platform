"""Validation rules for microbial genomics sample tables."""

import pandas as pd

REQUIRED_COLUMNS = frozenset(
    {"sample_id", "taxon", "read_count", "gc_content"}
)


def validate_dataframe(samples: pd.DataFrame) -> None:
    """Raise ValueError when a sample table violates the data contract."""
    missing = REQUIRED_COLUMNS.difference(samples.columns)
    if missing:
        missing_columns = ", ".join(sorted(missing))
        raise ValueError(f"Missing required columns: {missing_columns}")

    if samples.empty:
        raise ValueError("Sample data cannot be empty")

    if samples["sample_id"].isna().any() or samples["taxon"].isna().any():
        raise ValueError("sample_id and taxon cannot contain missing values")

    if (samples["read_count"] < 0).any():
        raise ValueError("read_count cannot be negative")

    if ((samples["gc_content"] < 0) | (samples["gc_content"] > 100)).any():
        raise ValueError("gc_content must be between 0 and 100")


__all__ = ["REQUIRED_COLUMNS", "validate_dataframe"]
