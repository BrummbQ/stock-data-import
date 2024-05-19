import os
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone
from decimal import Decimal

from .constants import StockMetaFields


def connect_stocks_table():
    table_name = os.environ["STOCKS_TABLE"]
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-3")
    return dynamodb.Table(table_name)


def connect_stocks_meta_table():
    meta_table_name = os.environ["STOCKS_META_TABLE"]
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-3")
    return dynamodb.Table(meta_table_name)


def add_stock_meta(stock_isin: str):
    meta_table = connect_stocks_meta_table()
    meta_table.put_item(Item={"ISIN": stock_isin, StockMetaFields.last_import.name: 0})


def fetch_stock_meta(stock_isin: str):
    meta_table = connect_stocks_meta_table()
    response = meta_table.get_item(
        Key={
            "ISIN": stock_isin,
        }
    )
    if "Item" not in response:
        return None
    return response["Item"]


def update_stock_meta(
    stock_isin: str, fnet_estimation: str | None = None, fnet_guv: str | None = None
):
    meta_table = connect_stocks_meta_table()
    update_expr_list = []
    expr_values = {}
    if fnet_estimation is not None:
        update_expr_list.append(
            f"{StockMetaFields.fnet_estimation_url.name} = :{StockMetaFields.fnet_estimation_url.name}"
        )
        expr_values[f":{StockMetaFields.fnet_estimation_url.name}"] = fnet_estimation
    if fnet_guv is not None:
        update_expr_list.append(
            f"{StockMetaFields.fnet_guv_url.name} = :{StockMetaFields.fnet_guv_url.name}"
        )
        expr_values[f":{StockMetaFields.fnet_guv_url.name}"] = fnet_guv

    update_expr = ", ".join(update_expr_list)

    meta_table.update_item(
        Key={"ISIN": stock_isin},
        UpdateExpression=f"SET {update_expr}",
        ExpressionAttributeValues=expr_values,
    )


def fetch_oldest_stock_meta() -> str | None:
    meta_table = connect_stocks_meta_table()
    response = meta_table.scan()
    if "Items" in response:
        # sort by last_import
        sorted_stocks = sorted(
            response["Items"], key=lambda item: item[StockMetaFields.last_import.name]
        )
        if len(sorted_stocks):
            return sorted_stocks[0]["ISIN"]

    return None


def fetch_stock_data(stock_isin: str):
    table = connect_stocks_table()
    response = table.query(KeyConditionExpression=Key("ISIN").eq(stock_isin))
    items = response["Items"]
    return items


def update_stock_data(stock_isin: str, year: int, item: dict):
    # item empty
    if not item:
        return

    # generate update expr
    update_expr = list(map(lambda i: f"{i} = :{i}", list(item.keys())))
    update_expr = ", ".join(update_expr)

    # generate expr attr vals
    expr_attr = {}
    for key in item:
        expr_attr[f":{key}"] = item[key]

    print("Write item", item)
    print("Expr", update_expr)

    # write item
    table = connect_stocks_table()
    table.update_item(
        Key={"ISIN": stock_isin, "Year": year},
        UpdateExpression=f"SET {update_expr}",
        ExpressionAttributeValues=expr_attr,
    )


def update_last_import(stock_isin: str):
    meta_table = connect_stocks_meta_table()
    now = datetime.now(timezone.utc).timestamp()
    meta_table.update_item(
        Key={"ISIN": stock_isin},
        UpdateExpression=f"SET {StockMetaFields.last_import.name} = :val1",
        ExpressionAttributeValues={":val1": Decimal(str(now))},
    )
