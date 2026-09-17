terraform {
  required_version = ">= 1.4.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  region                      = "us-east-1"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  s3_use_path_style           = true

  endpoints {
    apigateway = "http://localhost:4566"
    cloudwatch = "http://localhost:4566"
    dynamodb   = "http://localhost:4566"
    iam        = "http://localhost:4566"
    lambda     = "http://localhost:4566"
    s3         = "http://localhost:4566"
  }
}

resource "aws_s3_bucket" "raw_data" {
  bucket = "microbial-raw"
}

resource "aws_s3_bucket" "results" {
  bucket = "microbial-results"
}

resource "aws_dynamodb_table" "metadata" {
  name         = "microbial-metadata"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "dataset_id"

  attribute {
    name = "dataset_id"
    type = "S"
  }
}

resource "aws_iam_role" "lambda_execution" {
  name = "lambda-basic-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

locals {
  lambda_source = "../../src/lambda_handlers/microbial_processor.py"
}

data "archive_file" "processor" {
  type        = "zip"
  source_file = local.lambda_source
  output_path = "../artifacts/microbial-processor.zip"
}

resource "aws_lambda_function" "processor" {
  function_name = "microbial-processor"
  runtime       = "python3.12"
  handler       = "microbial_processor.handler"
  role          = aws_iam_role.lambda_execution.arn
  filename      = data.archive_file.processor.output_path
  timeout       = 30
  memory_size   = 128
}

resource "aws_s3_bucket_notification" "raw_trigger" {
  bucket = aws_s3_bucket.raw_data.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.processor.arn
    events              = ["s3:ObjectCreated:*"]
  }
}

resource "aws_apigatewayv2_api" "microbial_api" {
  name          = "microbial-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.microbial_api.id
  name        = "$default"
  auto_deploy = true
}
