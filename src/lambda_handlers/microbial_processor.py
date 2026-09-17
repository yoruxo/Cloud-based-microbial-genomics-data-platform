import csv
import io
import json
import os
from urllib.parse import unquote_plus

import boto3

REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
S3 = boto3.client("s3", region_name=REGION, endpoint_url=ENDPOINT_URL)


def handler(event, context):
    """Process uploaded genomic CSV files stored in the raw S3 bucket."""
    records = event.get("Records", [])
    processed = []

    for record in records:
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])

        obj = S3.get_object(Bucket=bucket, Key=key)
        payload = obj["Body"].read().decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(payload)))

        result = {
            "source": key,
            "row_count": len(rows),
            "columns": list(rows[0].keys()) if rows else [],
            "samples": rows,
        }

        target_key = f"processed/{key}.summary.json"
        S3.put_object(
            Bucket="microbial-results",
            Key=target_key,
            Body=json.dumps(result, default=str).encode("utf-8"),
            ContentType="application/json",
        )
        processed.append({"bucket": bucket, "key": key, "target": target_key})

    return {
        "status": "ok",
        "processed": processed,
    }
