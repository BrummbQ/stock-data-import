import os
import requests
import json
from bs4 import BeautifulSoup
from io import StringIO
import pandas as pd
from openai import OpenAI
import traceback
from typing import Any

from .lib.constants import SYSTEM_PROMPT_TABLES, StockDataKey, PageCurrencies
from .lib.data import fetch_oldest_stock_meta, update_last_import, update_stock_data
from .lib.helper import find_curr, text_currency_to_float
from .lib.url import search_boerse_de_url, search_fnet_estimation_url, search_fnet_guv_url
from .lib.data_helper import dataframe_to_items
from .lib.table_helper import find_table_entries


def handler(event, context):
    stock_isin = None
    if (
        event is None
        or "queryStringParameters" not in event
        or "ISIN" not in event["queryStringParameters"]
    ):
        stock_isin = fetch_oldest_stock_meta()
    else:
        # import this
        stock_isin = event["queryStringParameters"]["ISIN"]

    if stock_isin is None:
        raise Exception("Could not find ISIN")

    scrappey_key = os.environ["SCRAPPEY_API_KEY"]
    openai_key = os.environ["OPENAI_API_KEY"]

    print("Start importing stock", stock_isin)

    # boerse.de
    boerse_de_url = search_boerse_de_url(stock_isin)
    process_import(scrappey_key, boerse_de_url, stock_isin, openai_key)

    # finanzen.net GUV
    f_net_guv_url = search_fnet_guv_url(stock_isin)
    if f_net_guv_url is not None:
        process_import(scrappey_key, f_net_guv_url, stock_isin, openai_key)

    # finanzen.net Estimation
    f_net_estimation_url = search_fnet_estimation_url(stock_isin)
    if f_net_estimation_url is not None:
        process_import(scrappey_key, f_net_estimation_url, stock_isin, openai_key)

    update_last_import(stock_isin)


def process_import(scrappey_key: str, url: str, stock_isin: str, openai_key: str):
    try:
        page_html = fetch_html(scrappey_key, url)
        process_html(stock_isin, openai_key, page_html)
    except Exception as e:
        print("Error importing:", url)
        print(e)
        traceback.print_tb(e.__traceback__)


def process_html(stock_isin: str, openai_key: str, page_html: str):
    stock_dfs = pd.read_html(StringIO(page_html), decimal=",", thousands=".")
    page_tables = tables_from_dfs(stock_dfs)
    page_titles = titles_from_html(page_html)
    currencies = fetch_currencies(openai_key, page_tables, page_titles)
    #tables_metadata = fetch_tables_metadata(openai_key, page_tables)
    tables_metadata = find_table_entries(stock_dfs)
    stock_df = create_stock_df(currencies, tables_metadata, stock_dfs)
    if stock_df is not None:
        persist_df(stock_df, stock_isin)


def fetch_html(api_key: str, source_url: str) -> str:
    print("Scraping url", source_url)

    url = f"https://publisher.scrappey.com/api/v1?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"cmd": "request.get", "url": source_url, "requestType": "request"}

    response = requests.post(url, headers=headers, json=data)

    # Handle the response
    if response.status_code == 200:
        response_content = response.json()
        if "solution" in response_content:
            html = response_content["solution"]["response"]
            print("Page html size:", len(html))
            return html

    raise Exception(f"Cant fetch html: {response_content["data"]}")


def format_df_rows(d: pd.DataFrame):
    first_col = d.columns[0]
    rows = ""
    for row in d[first_col]:
        rows += f"{row}\n"
    return rows


def tables_from_dfs(dfs) -> str:
    rows_dfs = [
        f'<table id="{i}">\n{format_df_rows(df)}</table>' for i, df in enumerate(dfs)
    ]
    tables = "\n".join(rows_dfs)
    print("Extracted tables:", tables)
    return tables


def titles_from_html(page_html: str) -> str:
    page_parser = BeautifulSoup(page_html, "html.parser")
    html_tables_titles = page_parser.select("h2:has(+ * table), h2:has(+ table)")
    html_tables_titles_str = ""
    for col in html_tables_titles:
        html_tables_titles_str += f"\n{str(col)}"
    print("Extracted page titles:", html_tables_titles_str)
    return html_tables_titles_str


def fetch_currencies(api_key: str, page_tables: str, page_titles: str) -> PageCurrencies | None:
    client = OpenAI(api_key=api_key)

    prompt = f"""
    Following document between TEXTSTART and TEXTEND contains tables with stock fundamentals. Extract the currencies to this format:


    {{
        "dataCurrency": "USD",
        "salesCurrency": "USD"
    }}

    TEXTSTART
    {page_titles}

    {page_tables}
    TEXTEND
    """

    response_body_cur = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-3.5-turbo",
    )
    content = response_body_cur.choices[0].message.content
    if content is None:
        return None
    currencies = json.loads(content)
    print("Fetched currencies", currencies)
    return currencies


def fetch_tables_metadata(api_key: str, page_tables: str) -> str | None:
    client = OpenAI(api_key=api_key)

    prompt = f"""
    {page_tables}
    """

    response_body = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT_TABLES,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        model="ft:gpt-3.5-turbo-0125:personal::9IEIVkmH:ckpt-step-27",
        max_tokens=500,
        temperature=0.8,
    )
    table_data = response_body.choices[0].message.content
    print("Extracted table data:", table_data)
    return table_data


def read_table_row(
    section: str, key: int, row: int, dfs: list[pd.DataFrame], currency=None, multiply=False
) -> pd.DataFrame:
    if key == None or row == None:
        return pd.DataFrame()
    table_df: pd.DataFrame = dfs[key]
    years: list[int] = []
    data = []
    for col in table_df:
        try:
            year: Any = col
            if isinstance(year, str):
                # reformat year (13/14 -> 2014)
                if "/" in year:
                    year = 2000 + int(year.split("/")[-1])
                # reformat year (2014e -> 2014)
                if "e" in year:
                    year = year.split("e")[0]

            # allow 2000, 2014, 2099
            if int(year) and len(str(year)) == 4:
                years.append(int(year))
                formatted_data = table_df[col][row]
                # find curr in entry: 1.200,23 EUR -> EUR
                data_currency = find_curr(formatted_data)
                if data_currency is not None:
                    # remove curr from entry: 1.200,23 EUR -> 1200,23
                    formatted_data = text_currency_to_float(formatted_data.split(data_currency)[0].strip())
                    # overwrite with currency from entry
                    currency = data_currency

                if multiply:
                    mrdStr = "Mrd."
                    # multiply mrd numbers
                    if isinstance(formatted_data, str) and mrdStr in formatted_data:
                        formatted_data = formatted_data.replace(mrdStr, "").strip()
                        formatted_data = int(
                            text_currency_to_float(formatted_data) * 1000000000
                        )
                    # multiply mio numbers
                    else:
                        try:
                            formatted_data = int(
                                text_currency_to_float(formatted_data) * 1000000
                            )
                        except Exception as e:
                            pass
                if currency is not None:
                    formatted_data = f"{formatted_data} {currency}"
                if (
                    (section == StockDataKey.DIVIDEND_YIELD.value or section == StockDataKey.EQUITY_RATIO.value)
                ):
                    # 1.28 -> 1.28%
                    if "%" not in str(formatted_data):
                        formatted_data = f"{formatted_data}%"
                                    # 1.28 % -> 1.28%
                if isinstance(formatted_data, str) and "%" in formatted_data:
                    formatted_data = formatted_data.replace(" ", "")
                # dont include stock count = 0
                if section == StockDataKey.STOCK_COUNT.value and formatted_data == 0:
                    formatted_data = None

                data.append(formatted_data)
        except ValueError as e:
            pass

    return pd.DataFrame({"Year": years, section: data})


def create_stock_df(
    currency_data, tables_metadata: str, dfs: list[pd.DataFrame]
) -> pd.DataFrame | None:
    if tables_metadata is None or tables_metadata.strip() == "":
        return None

    tables_df = pd.read_csv(
        StringIO(tables_metadata), skipinitialspace=True, delimiter=";"
    ).drop_duplicates(["category"])

    data_currency = currency_data["dataCurrency"]
    sales_currency = currency_data["salesCurrency"]

    formatted_dfs = []
    for i in tables_df.index:
        section = tables_df["category"][i]
        table = int(tables_df["table"][i])
        col = tables_df["column"][i]
        first_col = dfs[table].columns[0]
        col_list = dfs[table][first_col].to_list()

        # normalize characters
        col = str(col).replace("\xad", "")
        col_list = list(map(lambda x: str(x).replace("\xad", ""), col_list))
        if col not in col_list:
            print(f"Error: Didnt found {col} in {col_list}")
            continue

        col_pos = col_list.index(col)
        currency = None
        multiply = False
        if section == StockDataKey.SALES.value:
            currency = sales_currency
            multiply = True
        elif section == StockDataKey.EBIT.value or section == StockDataKey.TOTAL_DEBT.value or section == StockDataKey.MARKET_CAP.value:
            currency = data_currency
            multiply = True
        elif section == StockDataKey.STOCK_COUNT.value:
            multiply = True
        elif section in [
            StockDataKey.DIVIDEND_PER_SHARE.value,
            StockDataKey.SALES_PER_SHARE.value,
            StockDataKey.BOOK_PER_SHARE.value,
            StockDataKey.CASHFLOW_PER_SHARE.value,
            StockDataKey.EARNINGS_PER_SHARE.value,
        ]:
            currency = data_currency

        formatted_dfs.append(
            read_table_row(section, table, col_pos, dfs, currency, multiply)
        )

    complete_df: pd.DataFrame | None = None
    for df in formatted_dfs:
        print("Formatted DF:", df)
        if not df.empty:
            if complete_df is None:
                complete_df = df
            else:
                complete_df = complete_df.merge(df, on="Year", how="outer")

    print("Stock dataframe:", complete_df)
    return complete_df               


def persist_df(stock_df: pd.DataFrame, stock_isin: str):
    items = dataframe_to_items(stock_df)
    for [item, year] in items:
        update_stock_data(stock_isin, year, item)
