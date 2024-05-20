import io
from datetime import datetime, timezone
import csv


from .lib.data import fetch_stock_meta, add_stock_meta
from .lib.constants import StockDataKey
from .lib.data_completer import fill_missing_values


def handler(event, context):
    stock_isin = event["queryStringParameters"]["ISIN"]

    # check if stock in meta table
    meta_item = fetch_stock_meta(stock_isin)
    if meta_item is None:
        print("Adding new stock entry:", stock_isin)
        add_stock_meta(stock_isin)
    else:
        print("Stock entry found:", meta_item)

    fields = [
        StockDataKey.SALES,
        StockDataKey.SALES_PER_SHARE,
        StockDataKey.EARNINGS_PER_SHARE,
        StockDataKey.CASHFLOW_PER_SHARE,
        StockDataKey.BOOK_PER_SHARE,
        StockDataKey.DIVIDEND_PER_SHARE,
        StockDataKey.DIVIDEND_YIELD,
        StockDataKey.EQUITY_RATIO,
        StockDataKey.MARKET_CAP,
        StockDataKey.EBIT,
        StockDataKey.TOTAL_DEBT,
        StockDataKey.KGV,
        StockDataKey.KBV,
        StockDataKey.KUV,
        StockDataKey.KCV,
        StockDataKey.EMPLOYEE_COUNT,
        StockDataKey.STOCK_COUNT,
        StockDataKey.PRICE_PER_SHARE,
    ]
    fields = map(lambda i: i.value, fields)

    # read stocks data and create df
    data_df_raw = fill_missing_values(stock_isin)
    if data_df_raw is None:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/csv"},
            "body": "",
        }

    data_df_raw = data_df_raw.reindex(columns=fields)
    data_df = data_df_raw.transpose()
    # filter df by years
    current_year = datetime.now(timezone.utc).year
    min_year = current_year - 2
    max_year = current_year + 4
    dropped_cols = []
    for col in data_df:
        if col < min_year or col > max_year:
            dropped_cols.append(col)
    data_df = data_df.drop(columns=dropped_cols)

    # write csv
    output_csv = io.StringIO()
    data_df.to_csv(output_csv, decimal=",", quoting=csv.QUOTE_ALL, sep=";")
    csv_string = output_csv.getvalue().replace(".", ",")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/csv"},
        "body": csv_string,
    }
