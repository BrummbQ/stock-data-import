from duckduckgo_search import DDGS
import urllib.parse

from .data import fetch_stock_meta, update_stock_meta
from .constants import StockMetaFields


def search_boerse_de_url(stock_isin: str) -> str:
    BOERSE_DE_URL = "https://www.boerse.de/fundamental-analyse/Aktie/"
    return BOERSE_DE_URL + stock_isin


def search_fnet_stock_name(stock_isin: str) -> str | None:
    query = f"site:finanzen.net isin {stock_isin} Aktie"
    results = DDGS().text(
        query,
        max_results=1,
    )
    if len(results):
        stock_url = results[0]["href"]
        url_parts = urllib.parse.urlparse(stock_url)
        url_slug = url_parts.path.rsplit("/", 1)[-1]
        stock_url = url_slug.replace("-aktie", "")
        print("Found fnet stock name:", stock_url)
        return stock_url

    return None


def search_fnet_estimation_url(stock_isin: str) -> str | None:
    stock_meta = fetch_stock_meta(stock_isin)
    if stock_meta and StockMetaFields.fnet_estimation_url.name in stock_meta:
        stock_url = stock_meta[StockMetaFields.fnet_estimation_url.name]
        print("Found fnet estimation url from db:", stock_url)
        return stock_url

    query = f"site:finanzen.net isin {stock_isin} schaetzungen prognosen & erwartungen"
    results = query_ddg(query)

    for result in results:
        if "schaetzungen" in result["href"]:
            stock_url = result["href"]
            print("Found fnet estimation url:", stock_url)
            update_stock_meta(stock_isin, fnet_estimation=stock_url)
            return stock_url

    return None


def search_fnet_guv_url(stock_isin: str) -> str | None:
    stock_meta = fetch_stock_meta(stock_isin)
    if stock_meta and StockMetaFields.fnet_guv_url.name in stock_meta:
        stock_url = stock_meta[StockMetaFields.fnet_guv_url.name]
        print("Found fnet guv url from db:", stock_url)
        return stock_url

    query = f"site:finanzen.net isin {stock_isin} Bilanz & GUV"
    results = query_ddg(query)

    for result in results:
        if "bilanz" in result["href"]:
            stock_url = result["href"]
            print("Found fnet guv url:", stock_url)
            update_stock_meta(stock_isin, fnet_guv=stock_url)
            return stock_url

    return None


def query_ddg(query: str):
    try:
        return DDGS().text(query, max_results=3, backend="html")
    except Exception as e:
        print(e)
        return []
