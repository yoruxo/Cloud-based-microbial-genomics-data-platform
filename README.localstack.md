# LocalStack AWS-style structure

This project includes a LocalStack setup that mirrors the architecture described in the outline:

- User uploads raw genomic CSV files into an S3 bucket.
- S3 triggers a Lambda function.
- The Lambda validates and summarizes the data.
- Results are stored in a second S3 bucket.
- Metadata is saved in DynamoDB.
- API Gateway exposes the service locally.

## Start the stack

```powershell
docker compose up -d
```

## Check LocalStack endpoints

```powershell
curl http://localhost:4566/_localstack/health
```

## Inspect the AWS-style resources

```powershell
awslocal s3 ls
awslocal lambda list-functions
awslocal dynamodb list-tables
```

## Upload a sample file

```powershell
awslocal s3 cp .\data\example.csv s3://microbial-raw/
```

## Read processed output

```powershell
awslocal s3 ls s3://microbial-results
```

## Stop the stack

```powershell
docker compose down
```
