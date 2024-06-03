import requests
from urllib.parse import quote
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from decimal import Decimal

from .constants import TradingviewStoryItem, StockStoryItem


TRADINGVIEW_BASE_URL = "https://www.tradingview.com"


def find_stock_symbol(stock_isin: str) -> str:
    print("Try to find tradingview symbol for", stock_isin)
    symbol_api_url = f"https://symbol-search.tradingview.com/symbol_search/v3/?text={stock_isin}&hl=1&exchange=&lang=en&search_type=stocks&domain=production&sort_by_country=US"
    headers = {
        "accept": "*/*",
        "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "origin": "https://www.tradingview.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://www.tradingview.com/",
        "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }

    symbol_response = requests.get(symbol_api_url, headers=headers)
    if symbol_response.status_code != 200:
        raise Exception("Failed to fetch tradingview stock symbol")

    symbol_data = symbol_response.json()

    if not len(symbol_data["symbols"]):
        raise Exception("Could not find tradingview symbols")

    first_symbol = symbol_data["symbols"][0]
    tradingview_symbol = f"{first_symbol['exchange']}:{first_symbol['symbol']}"
    print("Found tradingview symbol:", tradingview_symbol)
    return tradingview_symbol


def fetch_stories(stock_isin: str) -> list[TradingviewStoryItem]:
    tradingview_symbol = find_stock_symbol(stock_isin)
    tradingview_symbol_escaped = quote(tradingview_symbol)
    stories_api_url = f"https://news-headlines.tradingview.com/v2/view/headlines/symbol?client=web&lang=en&section=&streaming=false&symbol={tradingview_symbol_escaped}"

    print("Fetching tradingview stories for", stock_isin)
    stories_response = requests.get(stories_api_url)
    if stories_response.status_code != 200:
        raise Exception("Failed to fetch tradingview story list")

    stories_data = stories_response.json()
    items = stories_data["items"]
    stories_result: list[TradingviewStoryItem] = []
    # only get the latest 50 stories
    for item in items[:50]:
        story_item = fetch_story(stock_isin, item)
        if story_item is not None:
            stories_result.append(story_item)

    return stories_result


def fetch_story(
    stock_isin: str, story_item: TradingviewStoryItem
) -> StockStoryItem | None:
    story_url = TRADINGVIEW_BASE_URL + story_item["storyPath"]

    print("Fetching tradingview story")
    story_response = requests.get(story_url)
    if story_response.status_code != 200:
        raise Exception("Failed to fetch tradingview story item")

    print("Fetched tradingview story", story_item["title"])
    story_data = story_response.text
    now = Decimal(str(datetime.now(timezone.utc).timestamp()))

    page_parser = BeautifulSoup(story_data, "html.parser")
    story_article = page_parser.select_one("div[aria-label='Main content'] article")
    if story_article is None or story_article.text == "":
        # fallback to script tag
        story_article = page_parser.select_one("div[aria-label='Main content'] script")

    # format and return result
    if story_article is not None and story_article.text != "":
        return {
            "ISIN": stock_isin,
            "source_url": story_url,
            "published_at": Decimal(story_item["published"]),
            "fetched_at": now,
            "text_content": story_article.text,
            "title": story_item["title"],
            "data_provider": story_item["provider"],
        }

    print("Could not find text content for story!", story_url)
    return None
