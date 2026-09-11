from pathlib import Path

from fastapi.testclient import TestClient

from src.api import create_app


def test_upload_list_and_retrieve_dataset(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    with open("data/example.csv", "rb") as sample_file:
        response = client.post(
            "/datasets",
            files={"file": ("example.csv", sample_file, "text/csv")},
        )

    assert response.status_code == 201
    metadata = response.json()
    assert metadata["row_count"] == 5
    assert metadata["filename"] == "example.csv"

    listed = client.get("/datasets")
    assert listed.status_code == 200
    assert listed.json()[0]["dataset_id"] == metadata["dataset_id"]
    assert listed.json()[0]["filename"] == "example.csv"

    retrieved = client.get(f"/datasets/{metadata['dataset_id']}")
    assert retrieved.status_code == 200
    assert retrieved.json()["records"][0]["sample_id"] == "sample-001"


def test_upload_rejects_invalid_dataset(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/datasets",
        files={
            "file": (
                "invalid.csv",
                "sample_id,taxon,read_count\na,E. coli,10\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 422
    assert "Missing required columns" in response.json()["detail"]