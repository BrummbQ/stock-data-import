from .lib.data import (
    fetch_oldest_stock_story_meta,
    add_stock_stories,
    update_last_story_import,
)
from .lib.story_scraper import fetch_stories


def handler(event, context):
    stock_isin = None
    if (
        event is None
        or "queryStringParameters" not in event
        or "ISIN" not in event["queryStringParameters"]
    ):
        stock_isin = fetch_oldest_stock_story_meta()
    else:
        # import this
        stock_isin = event["queryStringParameters"]["ISIN"]

    if stock_isin is None:
        raise Exception("Could not find ISIN")

    print("Start importing stocks stories for:", stock_isin)
    stories = fetch_stories(stock_isin)
    add_stock_stories(stories)
    update_last_story_import(stock_isin)
