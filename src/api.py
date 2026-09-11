"""HTTP API for storing and retrieving microbial sample datasets."""

from __future__ import annotations

import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from src.validation import validate_dataframe


class DatasetMetadata(BaseModel):
    """Metadata returned for an uploaded dataset."""

    dataset_id: str
    filename: str
    row_count: int
    columns: list[str]
    created_at: datetime


class DatasetResponse(DatasetMetadata):
    """A dataset and its validated sample records."""

    records: list[dict[str, object]]


def _default_data_dir() -> Path:
    return Path(os.getenv("MICROBIAL_DATA_DIR", "data/uploads"))


def create_app(data_dir: str | Path | None = None) -> FastAPI:
    """Create the API application, optionally using a custom storage directory."""
    storage_dir = Path(data_dir) if data_dir else _default_data_dir()
    storage_dir.mkdir(parents=True, exist_ok=True)

    app = FastAPI(
        title="Microbial Genomics Data API",
        description="Upload, validate, and retrieve microbial sample datasets.",
        version="1.0.0",
    )

    def dataset_path(dataset_id: str) -> Path:
        if not dataset_id or Path(dataset_id).name != dataset_id:
            raise HTTPException(status_code=404, detail="Dataset not found")
        path = storage_dir / f"{dataset_id}.csv"
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Dataset not found")
        return path

    def metadata_from(path: Path) -> DatasetMetadata:
        samples = pd.read_csv(path)
        metadata_path = path.with_suffix(".json")
        stored_metadata = json.loads(metadata_path.read_text())
        return DatasetMetadata(
            dataset_id=path.stem,
            filename=stored_metadata["filename"],
            row_count=len(samples),
            columns=list(samples.columns),
            created_at=datetime.fromtimestamp(
                path.stat().st_mtime, tz=timezone.utc
            ),
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/datasets",
        response_model=DatasetMetadata,
        status_code=status.HTTP_201_CREATED,
    )
    async def upload_dataset(file: UploadFile = File(...)) -> DatasetMetadata:
        """Validate and persist a CSV dataset."""
        if not file.filename or Path(file.filename).suffix.lower() != ".csv":
            raise HTTPException(status_code=415, detail="Only CSV files are supported")

        content = await file.read()
        try:
            samples = pd.read_csv(io.BytesIO(content))
            validate_dataframe(samples)
        except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        dataset_id = uuid4().hex
        path = storage_dir / f"{dataset_id}.csv"
        samples.to_csv(path, index=False)
        metadata = DatasetMetadata(
            dataset_id=dataset_id,
            filename=file.filename,
            row_count=len(samples),
            columns=list(samples.columns),
            created_at=datetime.now(timezone.utc),
        )
        path.with_suffix(".json").write_text(
            json.dumps(metadata.model_dump(mode="json")), encoding="utf-8"
        )
        return metadata

    @app.get("/datasets", response_model=list[DatasetMetadata])
    def list_datasets() -> list[DatasetMetadata]:
        return [metadata_from(path) for path in sorted(storage_dir.glob("*.csv"))]

    @app.get("/datasets/{dataset_id}", response_model=DatasetResponse)
    def get_dataset(dataset_id: str) -> DatasetResponse:
        path = dataset_path(dataset_id)
        metadata = metadata_from(path)
        records = pd.read_csv(path).to_dict(orient="records")
        return DatasetResponse(**metadata.model_dump(), records=records)

    return app


app = create_app()

__all__ = ["app", "create_app"]