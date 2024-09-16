import os
import json
import boto3

# client to invoke import function
lambda_client = boto3.client("lambda", region_name="eu-west-3")


def invoke_import_stocks(stock_isin: str):
    import_stocks_function = os.environ["IMPORT_STOCKS_FUNCTION"]
    payload = {"queryStringParameters": {"ISIN": stock_isin}}
    print(f"Invoke {import_stocks_function} for stock {stock_isin}")

    response = lambda_client.invoke(
        FunctionName=import_stocks_function,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload),
    )
    print(response)


def invoke_import_stocks_story(stock_isin: str):
    import_stocks_function = os.environ["IMPORT_STOCKS_STORY_FUNCTION"]
    payload = {"queryStringParameters": {"ISIN": stock_isin}}
    print(f"Invoke {import_stocks_function} for stock {stock_isin}")

    response = lambda_client.invoke(
        FunctionName=import_stocks_function,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload),
    )
    print(response)
