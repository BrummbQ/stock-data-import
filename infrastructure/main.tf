terraform {
 required_providers {
   aws = {
     source = "hashicorp/aws"
   }
 }
}
    
provider "aws" {
  region = "eu-west-3"
  shared_credentials_files = ["$HOME/.aws/credentials"]
}

variable "SCRAPPEY_API_KEY" {
  type = string
  sensitive = true
}

variable "OPENAI_API_KEY" {
  type = string
  sensitive = true
}

variable "HUGGINGFACEHUB_API_TOKEN" {
  type = string
  sensitive = true
}

resource "aws_dynamodb_table" "stocks_table" {
  name           = "stocks-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "ISIN"
  range_key      = "Year"
  table_class    = "STANDARD_INFREQUENT_ACCESS" 

  attribute {
    name = "ISIN"
    type = "S"
  }

  attribute {
    name = "Year"
    type = "N"
  }

  tags = {
    Environment = "production"
  }
}

resource "aws_dynamodb_table" "stocks_meta_table" {
  name           = "stocks-meta-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "ISIN"
  table_class    = "STANDARD_INFREQUENT_ACCESS" 

  attribute {
    name = "ISIN"
    type = "S"
  }

  tags = {
    Environment = "production"
  }
}

resource "aws_dynamodb_table" "stocks_story_table" {
  name           = "stocks-story-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "ISIN"
  range_key      = "source_url"
  table_class    = "STANDARD_INFREQUENT_ACCESS" 

  attribute {
    name = "ISIN"
    type = "S"
  }

  attribute {
    name = "source_url"
    type = "S"
  }

  tags = {
    Environment = "production"
  }
}

resource "aws_s3_bucket" "lambda_layer_source" {
  tags = {
    Description        = "Bucket for lambda layers"
  }
}

resource "aws_s3_object" "lambda_layer_object" {
  bucket = aws_s3_bucket.lambda_layer_source.id
  key    = "layer_content.zip"
  source = "../lambda-layer/layer_content.zip"
  source_hash  = "${filemd5("../lambda-layer/layer_content.zip")}"
}

resource "aws_lambda_layer_version" "lambda_python_layer" {
  s3_bucket  = aws_s3_bucket.lambda_layer_source.id
  s3_key     = aws_s3_object.lambda_layer_object.key
  layer_name = "lambda_python_layer"

  compatible_runtimes = ["python3.12"]
  compatible_architectures = ["arm64"]
  source_code_hash = "${filebase64sha256("../lambda-layer/layer_content.zip")}"
}

resource "aws_iam_role" "iam_for_lambda" {
 name = "iam_for_lambda"

 assume_role_policy = jsonencode({
   "Version" : "2012-10-17",
   "Statement" : [
     {
       "Effect" : "Allow",
       "Principal" : {
         "Service" : "lambda.amazonaws.com"
       },
       "Action" : "sts:AssumeRole"
     }
   ]
  })
}
          
resource "aws_iam_role_policy_attachment" "lambda_policy" {
   role = aws_iam_role.iam_for_lambda.name
   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
          
resource "aws_iam_role_policy" "lambda_role_policy" {
   name = "lambda_role_policy"
   role = aws_iam_role.iam_for_lambda.id
   policy = jsonencode({
      "Version" : "2012-10-17",
      "Statement" : [
        {
           "Effect" : "Allow",
           "Action" : ["dynamodb:*"],
           "Resource" : "${aws_dynamodb_table.stocks_table.arn}"
        },
        {
           "Effect" : "Allow",
           "Action" : ["dynamodb:*"],
           "Resource" : "${aws_dynamodb_table.stocks_meta_table.arn}"
        },
        {
           "Effect" : "Allow",
           "Action" : ["dynamodb:*"],
           "Resource" : "${aws_dynamodb_table.stocks_story_table.arn}"
        },
        {
          "Sid": "InvokeImportStocksLambdaPermission",
          "Effect": "Allow",
          "Action": ["lambda:InvokeFunction"],
          "Resource": "${aws_lambda_function.import_stocks_data.arn}"
        }
      ]
   })
}

data "archive_file" "lambdas_data_archive" {
 source_dir = "${path.module}/../app"
 excludes   = [
  "requirements.txt", ".mypy.ini", ".mypy_cache"
 ]
 output_path = "${path.module}/../app.zip"
 type = "zip"
}

resource "aws_lambda_function" "get_stocks_data" {
 environment {
   variables = {
     STOCKS_TABLE = aws_dynamodb_table.stocks_table.name
     STOCKS_META_TABLE = aws_dynamodb_table.stocks_meta_table.name
     IMPORT_STOCKS_FUNCTION = aws_lambda_function.import_stocks_data.arn
   }
 }
 memory_size = "128"
 runtime = "python3.12"
 architectures = ["arm64"]
 layers = [
  aws_lambda_layer_version.lambda_python_layer.arn,
  "arn:aws:lambda:eu-west-3:336392948345:layer:AWSSDKPandas-Python312-Arm64:6"
 ]
 handler = "stocks.get_stocks_data.handler"
 function_name = "get_stocks_data"
 timeout = 240
 role = aws_iam_role.iam_for_lambda.arn
 filename = data.archive_file.lambdas_data_archive.output_path
 source_code_hash = data.archive_file.lambdas_data_archive.output_base64sha256
}

resource "aws_cloudwatch_log_group" "stocks_data_log" {
  name = "/aws/lambda/${aws_lambda_function.get_stocks_data.function_name}"

  retention_in_days = 30
}

resource "aws_lambda_function" "import_stocks_data" {
 environment {
   variables = {
     STOCKS_TABLE = aws_dynamodb_table.stocks_table.name
     STOCKS_META_TABLE = aws_dynamodb_table.stocks_meta_table.name
     SCRAPPEY_API_KEY = var.SCRAPPEY_API_KEY
     OPENAI_API_KEY = var.OPENAI_API_KEY
   }
 }
 memory_size = "256"
 runtime = "python3.12"
 architectures = ["arm64"]
 layers = [
  aws_lambda_layer_version.lambda_python_layer.arn,
  "arn:aws:lambda:eu-west-3:336392948345:layer:AWSSDKPandas-Python312-Arm64:6"
 ]
 handler = "stocks.import_stocks_data.handler"
 function_name = "import_stocks_data"
 timeout = 240
 role = aws_iam_role.iam_for_lambda.arn
 filename = data.archive_file.lambdas_data_archive.output_path
 source_code_hash = data.archive_file.lambdas_data_archive.output_base64sha256
}

resource "aws_cloudwatch_log_group" "import_stocks_data_log" {
  name = "/aws/lambda/${aws_lambda_function.import_stocks_data.function_name}"

  retention_in_days = 30
}

resource "aws_lambda_function" "import_stocks_story" {
 environment {
   variables = {
     STOCKS_TABLE = aws_dynamodb_table.stocks_table.name
     STOCKS_META_TABLE = aws_dynamodb_table.stocks_meta_table.name
     STOCKS_STORY_TABLE = aws_dynamodb_table.stocks_story_table.name
     HUGGINGFACEHUB_API_TOKEN = var.HUGGINGFACEHUB_API_TOKEN
   }
 }
 memory_size = "256"
 runtime = "python3.12"
 architectures = ["arm64"]
 layers = [
  aws_lambda_layer_version.lambda_python_layer.arn,
  "arn:aws:lambda:eu-west-3:336392948345:layer:AWSSDKPandas-Python312-Arm64:6"
 ]
 handler = "stocks.import_stocks_story.handler"
 function_name = "import_stocks_story"
 timeout = 480
 role = aws_iam_role.iam_for_lambda.arn
 filename = data.archive_file.lambdas_data_archive.output_path
 source_code_hash = data.archive_file.lambdas_data_archive.output_base64sha256
}

resource "aws_cloudwatch_log_group" "import_stocks_story_log" {
  name = "/aws/lambda/${aws_lambda_function.import_stocks_story.function_name}"

  retention_in_days = 30
}

resource "aws_apigatewayv2_api" "lambda_stocks" {
  name          = "serverless_lambda_gw"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "lambda_stocks" {
  api_id = aws_apigatewayv2_api.lambda_stocks.id

  name        = "lambda_stocks_stage"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw.arn

    format = jsonencode({
      requestId               = "$context.requestId"
      sourceIp                = "$context.identity.sourceIp"
      requestTime             = "$context.requestTime"
      protocol                = "$context.protocol"
      httpMethod              = "$context.httpMethod"
      resourcePath            = "$context.resourcePath"
      routeKey                = "$context.routeKey"
      status                  = "$context.status"
      responseLength          = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
      }
    )
  }
}

resource "aws_apigatewayv2_integration" "stocks_data" {
  api_id = aws_apigatewayv2_api.lambda_stocks.id

  integration_uri    = aws_lambda_function.get_stocks_data.invoke_arn
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "stocks_data" {
  api_id = aws_apigatewayv2_api.lambda_stocks.id

  route_key = "GET /stocks-data"
  target    = "integrations/${aws_apigatewayv2_integration.stocks_data.id}"
}

resource "aws_cloudwatch_log_group" "api_gw" {
  name = "/aws/api_gw/${aws_apigatewayv2_api.lambda_stocks.name}"

  retention_in_days = 30
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_stocks_data.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.lambda_stocks.execution_arn}/*/*"
}

resource "aws_cloudwatch_event_rule" "import_stock_lambda_schedule" {
  name                = "import-stock-lambda-schedule"
  schedule_expression = "cron(34 0/1 * * ? *)"
}

resource "aws_cloudwatch_event_target" "trigger_import_stock_lambda_on_schedule" {
  rule      = aws_cloudwatch_event_rule.import_stock_lambda_schedule.name
  target_id = "lambda"
  arn       = aws_lambda_function.import_stocks_data.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_import_stock_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.import_stocks_data.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.import_stock_lambda_schedule.arn
}

resource "aws_cloudwatch_event_rule" "import_stock_story_lambda_schedule" {
  name                = "import-stock-story-lambda-schedule"
  schedule_expression = "cron(10 0/2 * * ? *)"
}

resource "aws_cloudwatch_event_target" "trigger_import_stock_story_lambda_on_schedule" {
  rule      = aws_cloudwatch_event_rule.import_stock_story_lambda_schedule.name
  target_id = "lambda"
  arn       = aws_lambda_function.import_stocks_story.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_import_stock_story_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.import_stocks_story.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.import_stock_story_lambda_schedule.arn
}