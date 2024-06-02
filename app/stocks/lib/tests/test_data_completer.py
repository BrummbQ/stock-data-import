import pandas as pd
import numpy as np
from unittest import TestCase, main
from stocks.lib.constants import StockDataKey
from stocks.lib.data_completer import calculate_kuv


class TestCalculateKuv(TestCase):
    def test_missing_columns(self):
        stock_df = pd.DataFrame()
        result = calculate_kuv(stock_df)
        self.assertTrue(result.empty)

    def test_calculate_kuv(self):
        stock_df = pd.DataFrame(
            {
                StockDataKey.PRICE_PER_SHARE.value: [10.0, 20.0, 30.0],
                StockDataKey.SALES_PER_SHARE.value: [100.0, 200.0, 300.0],
            }
        )
        result = calculate_kuv(stock_df)
        expected_result = pd.DataFrame(
            {
                StockDataKey.PRICE_PER_SHARE.value: [10.0, 20.0, 30.0],
                StockDataKey.SALES_PER_SHARE.value: [100.0, 200.0, 300.0],
                StockDataKey.KUV.value: [0.1, 0.1, 0.1],
            }
        )
        self.assertEqual(result.to_dict(), expected_result.to_dict())

    def test_existing_kuv_values(self):
        stock_df = pd.DataFrame(
            {
                StockDataKey.PRICE_PER_SHARE.value: [10.0, 20.0, 30.0],
                StockDataKey.SALES_PER_SHARE.value: [100.0, 200.0, 300.0],
                StockDataKey.KUV.value: [0.1, 0.2, 0.3],
            }
        )
        result = calculate_kuv(stock_df)
        expected_result = pd.DataFrame(
            {
                StockDataKey.PRICE_PER_SHARE.value: [10.0, 20.0, 30.0],
                StockDataKey.SALES_PER_SHARE.value: [100.0, 200.0, 300.0],
                StockDataKey.KUV.value: [0.1, 0.1, 0.1],
            }
        )
        self.assertEqual(result.to_dict(), expected_result.to_dict())


if __name__ == "__main__":
    main()
