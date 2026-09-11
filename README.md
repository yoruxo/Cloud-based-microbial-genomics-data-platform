# Cloud-Based Microbial Genomics Data Platform

A small starting point for validating and summarizing microbial genomics sample data before it is sent to cloud processing services.

## Project structure

```text
src/
  analysis.py       Load data and calculate summaries
  validation.py     Enforce the sample data contract
  api.py            Upload and retrieve validated datasets over HTTP
data/
  example.csv       Example input data
tests/
  test_analysis.py  Automated tests
```

## Setup

Use Python 3.10 or newer, then install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run the tests

From the project root:

```powershell
python -m pytest
```

## Use the analysis helpers

```python
from src.analysis import load_samples, quality_report, summarize_by_taxon

samples = load_samples("data/example.csv")
print(quality_report(samples))
print(summarize_by_taxon(samples))
```

Input CSV files must include `sample_id`, `taxon`, `read_count`, and `gc_content`. Read counts must be non-negative, and GC content must be between 0 and 100 percent.

## Run the API

Install the dependencies, then start the local service:

```powershell
python -m uvicorn src.api:app --reload
```

Upload a CSV with `curl`:

```powershell
curl.exe -F "file=@data/example.csv" http://127.0.0.1:8000/datasets
```

Use `GET /datasets` to list uploads, or `GET /datasets/{dataset_id}` to retrieve metadata and sample records. Uploaded files are stored in `data/uploads` by default; set `MICROBIAL_DATA_DIR` to use another directory.
