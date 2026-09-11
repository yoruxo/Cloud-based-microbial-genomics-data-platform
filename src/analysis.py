"""Analysis helpers for microbial genomics sample data."""

from pathlib import Path

import pandas as pd

from src.validation import REQUIRED_COLUMNS, validate_dataframe


def load_samples(path: str | Path) -> pd.DataFrame:
    """Load and validate a sample CSV file."""
    samples = pd.read_csv(path)
    validate_dataframe(samples)
    return samples


def summarize_by_taxon(samples: pd.DataFrame) -> pd.DataFrame:
    """Return sample counts and mean read counts grouped by taxon."""
    validate_dataframe(samples)
    summary = (
        samples.groupby("taxon", as_index=False)
        .agg(
            sample_count=("sample_id", "nunique"),
            mean_read_count=("read_count", "mean"),
            mean_gc_content=("gc_content", "mean"),
        )
        .sort_values("sample_count", ascending=False)
        .reset_index(drop=True)
    )
    return summary


def quality_report(samples: pd.DataFrame) -> dict[str, float | int]:
    """Return basic quality metrics for a validated sample table."""
    validate_dataframe(samples)
    return {
        "sample_count": int(samples["sample_id"].nunique()),
        "taxon_count": int(samples["taxon"].nunique()),
        "mean_read_count": float(samples["read_count"].mean()),
        "mean_gc_content": float(samples["gc_content"].mean()),
    }


__all__ = ["REQUIRED_COLUMNS", "load_samples", "quality_report", "summarize_by_taxon"]
