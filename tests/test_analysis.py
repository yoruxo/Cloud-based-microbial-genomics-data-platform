import pandas as pd
import pytest

from src.analysis import load_samples, quality_report, summarize_by_taxon
from src.validation import validate_dataframe


@pytest.fixture
def samples() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sample_id": ["a", "b", "c"],
            "taxon": ["E. coli", "E. coli", "B. subtilis"],
            "read_count": [100, 300, 200],
            "gc_content": [50.0, 52.0, 44.0],
        }
    )


def test_summarize_by_taxon(samples: pd.DataFrame) -> None:
    summary = summarize_by_taxon(samples)

    assert summary["taxon"].tolist() == ["E. coli", "B. subtilis"]
    assert summary["sample_count"].tolist() == [2, 1]
    assert summary.loc[0, "mean_read_count"] == 200


def test_quality_report(samples: pd.DataFrame) -> None:
    assert quality_report(samples) == {
        "sample_count": 3,
        "taxon_count": 2,
        "mean_read_count": 200.0,
        "mean_gc_content": pytest.approx(48.6666666667),
    }


def test_rejects_invalid_gc_content(samples: pd.DataFrame) -> None:
    samples.loc[0, "gc_content"] = 101

    with pytest.raises(ValueError, match="gc_content"):
        validate_dataframe(samples)


def test_loads_example_csv() -> None:
    samples = load_samples("data/example.csv")

    assert len(samples) == 5
    assert set(samples["taxon"]) == {
        "Escherichia coli",
        "Bacillus subtilis",
        "Pseudomonas aeruginosa",
    }
