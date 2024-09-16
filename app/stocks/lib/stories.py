import pandas as pd

from .constants import StockStoryFields
from .data import fetch_stock_stories


def stories_sentiment(stock_isin: str) -> None | pd.DataFrame:
    stories = fetch_stock_stories(stock_isin)
    if not len(stories):
        print("Could not find data for:", stock_isin)
        return None

    columns = [
        StockStoryFields.published_at.name,
        StockStoryFields.fetched_at.name,
        StockStoryFields.sentiment.name,
        StockStoryFields.source_url.name,
    ]
    stories_df = pd.DataFrame.from_records(
        stories, index="published_at", columns=columns
    ).sort_index()
    return stories_df
