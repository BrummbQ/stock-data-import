import io
import csv

from .lib.data import fetch_stock_meta, add_stock_meta
from .lib.stories import stories_sentiment
from .lib.function import invoke_import_stocks_story


def handler(event, context):
    stock_isin = event["queryStringParameters"]["ISIN"]

    # check if stock in meta table
    meta_item = fetch_stock_meta(stock_isin)
    if meta_item is None:
        print("Adding new stock entry:", stock_isin)
        add_stock_meta(stock_isin)
        # trigger import function
        invoke_import_stocks_story(stock_isin)
    else:
        print("Stock entry found:", meta_item)

    stories = stories_sentiment(stock_isin)

    # write csv
    output_csv = io.StringIO()
    stories.to_csv(output_csv, decimal=",", quoting=csv.QUOTE_ALL, sep=";")
    csv_string = output_csv.getvalue()

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/csv"},
        "body": csv_string,
    }
