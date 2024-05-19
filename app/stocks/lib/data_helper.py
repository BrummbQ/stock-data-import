import pandas as pd
import numpy
from decimal import Decimal

from .helper import is_number_optional_suffix
from .constants import StockDataKey


def dataframe_to_items(stock_df: pd.DataFrame):
    if stock_df is None:
        return []

    items = []

    for i in stock_df.index:
        item = {}
        for col in stock_df:
            val = stock_df[col][i]
            # numpy to python types
            if isinstance(val, numpy.generic):
                if numpy.isnan(val):
                    val = None
                else:
                    val = val.item()
            # float to decimal
            if isinstance(val, float):
                val = Decimal(str(val))

            # filter empty values
            if (
                is_number_optional_suffix(val)
                # filter out year
                and col != "Year"
                and col in [el.value for el in StockDataKey]
            ):
                item[col] = val

        year = stock_df["Year"][i]
        if isinstance(year, numpy.generic):
            year = year.item()

        items.append([item, year])

    return items
