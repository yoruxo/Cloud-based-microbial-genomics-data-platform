#!/usr/bin/env bash
set -euo pipefail

# Wait until LocalStack is responding before creating AWS resources.
for _ in $(seq 1 30); do
  if curl -fsS http://localhost:4566/_localstack/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

awslocal s3 mb s3://microbial-raw --region us-east-1 || true
awslocal s3 mb s3://microbial-results --region us-east-1 || true

awslocal dynamodb create-table \
  --table-name microbial-metadata \
  --attribute-definitions AttributeName=dataset_id,AttributeType=S \
  --key-schema AttributeName=dataset_id,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region us-east-1 || true

python - <<'PY'
import json, pathlib
project = pathlib.Path('/opt/project')
source = project / 'src' / 'lambda_handlers' / 'microbial_processor.py'
zip_path = pathlib.Path('/tmp/localstack/microbial-processor.zip')
zip_path.parent.mkdir(parents=True, exist_ok=True)
import zipfile
with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    zf.write(source, arcname='microbial_processor.py')

notification = {
    'LambdaConfigurations': [
        {
            'LambdaFunctionArn': 'arn:aws:lambda:us-east-1:000000000000:function:microbial-processor',
            'Events': ['s3:ObjectCreated:*'],
        }
    ]
}
(pathlib.Path('/tmp/localstack/s3-notification.json')).write_text(json.dumps(notification), encoding='utf-8')
PY

awslocal iam create-role \
  --role-name lambda-basic-execution \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
  --region us-east-1 || true

awslocal lambda create-function \
  --function-name microbial-processor \
  --runtime python3.12 \
  --handler microbial_processor.handler \
  --role arn:aws:iam::000000000000:role/lambda-basic-execution \
  --zip-file fileb:///tmp/localstack/microbial-processor.zip \
  --timeout 30 \
  --memory-size 128 \
  --region us-east-1 || true

awslocal s3api put-bucket-notification-configuration \
  --bucket microbial-raw \
  --notification-configuration file:///tmp/localstack/s3-notification.json \
  --region us-east-1 || true

awslocal apigateway create-rest-api --name microbial-api --region us-east-1 >/tmp/localstack/api-id.txt 2>/dev/null || true

printf '\nLocalStack bootstrap complete.\n' 
printf 'S3 raw bucket: s3://microbial-raw\n'
printf 'S3 results bucket: s3://microbial-results\n'
printf 'DynamoDB table: microbial-metadata\n'
printf 'Lambda: microbial-processor\n'
printf 'Endpoint: http://localhost:4566\n'
