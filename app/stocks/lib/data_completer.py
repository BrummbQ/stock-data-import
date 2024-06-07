import pandas as pd
import numpy as np
from typing import TypeGuard

from .helper import find_curr, text_to_float
from .constants import StockDataKey
from .data import fetch_stock_data


def is_valid_float(value) -> TypeGuard[float]:
    return value is not None and value is not np.nan and value != 0


def calculate_pps(stock_df: pd.DataFrame) -> pd.DataFrame:
    if (
        StockDataKey.EARNINGS_PER_SHARE.value not in stock_df
        or StockDataKey.KGV.value not in stock_df
    ):
        return stock_df

    pps_list: list[str | float] = []

    for i in stock_df.index:
        EPS = text_to_float(stock_df[StockDataKey.EARNINGS_PER_SHARE.value][i])
        KGV = text_to_float(stock_df[StockDataKey.KGV.value][i])
        if is_valid_float(EPS) and is_valid_float(KGV):
            curr = find_curr(stock_df[StockDataKey.EARNINGS_PER_SHARE.value][i])
            PPS = EPS * KGV
            pps_list.append(f"{PPS:.2f} {curr}")
        else:
            pps_list.append(np.nan)

    if len(pps_list):
        stock_df[StockDataKey.PRICE_PER_SHARE.value] = pps_list

    return stock_df


def calculate_kbv(stock_df: pd.DataFrame) -> pd.DataFrame:
    kbv_list = []
    if (
        StockDataKey.BOOK_PER_SHARE.value not in stock_df
        or StockDataKey.PRICE_PER_SHARE.value not in stock_df
    ):
        return stock_df

    for i in stock_df.index:
        KBV = np.nan
        if StockDataKey.KBV.value in stock_df:
            KBV = stock_df[StockDataKey.KBV.value][i]
        BPS = text_to_float(stock_df[StockDataKey.BOOK_PER_SHARE.value][i])
        PPS = text_to_float(stock_df[StockDataKey.PRICE_PER_SHARE.value][i])
        if is_valid_float(BPS) and is_valid_float(PPS):
            KBV = PPS / BPS
            KBV = float("{:.2f}".format(KBV))
            kbv_list.append(KBV)
        else:
            kbv_list.append(KBV)

    if len(kbv_list):
        stock_df[StockDataKey.KBV.value] = kbv_list

    return stock_df


def calculate_stock_count(stock_df: pd.DataFrame) -> pd.DataFrame:
    if StockDataKey.STOCK_COUNT.value in stock_df:
        # drop stupid 0 values
        stock_df[StockDataKey.STOCK_COUNT.value] = stock_df[
            StockDataKey.STOCK_COUNT.value
        ].replace(0, np.nan)
        stock_df[StockDataKey.STOCK_COUNT.value] = stock_df[
            StockDataKey.STOCK_COUNT.value
        ].ffill()

    return stock_df


def calculate_sps(stock_df: pd.DataFrame) -> pd.DataFrame:
    if (
        StockDataKey.SALES_PER_SHARE.value not in stock_df
        or StockDataKey.SALES.value not in stock_df
        or StockDataKey.STOCK_COUNT.value not in stock_df
    ):
        return stock_df

    sps_list = []

    for i in stock_df.index:
        sps_value = stock_df[StockDataKey.SALES_PER_SHARE.value][i]
        sales_value = text_to_float(stock_df[StockDataKey.SALES.value][i])
        sales_curr = find_curr(stock_df[StockDataKey.SALES.value][i])
        stock_count_value = text_to_float(stock_df[StockDataKey.STOCK_COUNT.value][i])
        if (
            is_valid_float(sales_value)
            and is_valid_float(stock_count_value)
            and sales_curr is not None
        ):
            sps_value = sales_value / stock_count_value
            sps_list.append(f"{sps_value:.2f} {sales_curr}")
        else:
            sps_list.append(sps_value)

    if len(sps_list):
        stock_df[StockDataKey.SALES_PER_SHARE.value] = sps_list

    return stock_df


def calculate_kuv(stock_df: pd.DataFrame) -> pd.DataFrame:
    if (
        StockDataKey.PRICE_PER_SHARE.value not in stock_df
        or StockDataKey.SALES_PER_SHARE.value not in stock_df
    ):
        return stock_df

    kuv_list = []

    for i in stock_df.index:
        kuv_value = np.nan
        if StockDataKey.KUV.value in stock_df:
            kuv_value = stock_df[StockDataKey.KUV.value][i]
        sps_value = text_to_float(stock_df[StockDataKey.SALES_PER_SHARE.value][i])
        pps_value = text_to_float(stock_df[StockDataKey.PRICE_PER_SHARE.value][i])
        if is_valid_float(sps_value) and is_valid_float(pps_value):
            kuv_value = pps_value / sps_value
            kuv_list.append(float("{:.2f}".format(kuv_value)))
        else:
            kuv_list.append(kuv_value)

    if len(kuv_list):
        stock_df[StockDataKey.KUV.value] = kuv_list

    return stock_df


def fill_missing_values(stock_isin: str) -> None | pd.DataFrame:
    data = fetch_stock_data(stock_isin)
    if not len(data):
        print("Could not find data for:", stock_isin)
        return None

    stock_df = pd.DataFrame.from_records(data, index="Year")

    stock_df = calculate_stock_count(stock_df)
    stock_df = calculate_pps(stock_df)
    stock_df = calculate_kbv(stock_df)
    stock_df = calculate_sps(stock_df)
    stock_df = calculate_kuv(stock_df)
    # forward fill missing values
    stock_df = stock_df.ffill()

    return stock_df
