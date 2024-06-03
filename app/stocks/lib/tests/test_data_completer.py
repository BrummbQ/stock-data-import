import pandas as pd
import numpy as np
from unittest import TestCase, main
from stocks.lib.constants import StockDataKey
from stocks.lib.data_completer import calculate_kuv, is_valid, calculate_sps


class TestIsValid(TestCase):
    def test_is_valid(self):
        self.assertTrue(is_valid(1))
        self.assertFalse(is_valid(None))
        self.assertFalse(is_valid(np.nan))
        self.assertFalse(is_valid(0))
        self.assertTrue(is_valid(""))
        self.assertTrue(is_valid("hello"))


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


class TestCalculateSPS(TestCase):
    def test_all_columns_present_valid_values(self):
        # Test when all required columns are present and all values are valid
        stock_df = pd.DataFrame(
            {
                StockDataKey.SALES_PER_SHARE.value: [10.0, 20.0, 30.0],
                StockDataKey.SALES.value: ["100.0", "200.0", "300.0"],
                StockDataKey.STOCK_COUNT.value: [100.0, 200.0, 300.0],
            }
        )
        expected_result = pd.DataFrame(
            {
                StockDataKey.SALES_PER_SHARE.value: [10.0, 20.0, 30.0],
                StockDataKey.SALES.value: ["100.0", "200.0", "300.0"],
                StockDataKey.STOCK_COUNT.value: [100.0, 200.0, 300.0],
            },
        )
        result = calculate_sps(stock_df)
        self.assertEqual(result.to_dict(), expected_result.to_dict())

    def test_all_columns_present_invalid_values(self):
        # Test when all required columns are present but some values are invalid
        stock_df = pd.DataFrame(
            {
                StockDataKey.SALES_PER_SHARE.value: [10.0, 20.0, 30.0],
                StockDataKey.SALES.value: ["100.0", np.nan, "300.0"],
                StockDataKey.STOCK_COUNT.value: [100.0, 200.0, 300.0],
            }
        )
        expected_result = pd.DataFrame(
            {
                StockDataKey.SALES_PER_SHARE.value: [10.0, 20.0, 30.0],
                StockDataKey.SALES.value: ["100.0", np.nan, "300.0"],
                StockDataKey.STOCK_COUNT.value: [100.0, 200.0, 300.0],
            }
        )
        result = calculate_sps(stock_df)
        self.assertEqual(result.to_dict(), expected_result.to_dict())

    def test_calculate_sps(self):
        # Test when all required columns are present but some values are invalid
        stock_df = pd.DataFrame(
            {
                StockDataKey.SALES_PER_SHARE.value: [10.0, 0, 0],
                StockDataKey.SALES.value: ["100 EUR", "200 EUR", "300 EUR"],
                StockDataKey.STOCK_COUNT.value: [100.0, 200.0, 300.0],
            }
        )
        expected_result = pd.DataFrame(
            {
                StockDataKey.SALES_PER_SHARE.value: [
                    "1.00 EUR",
                    "1.00 EUR",
                    "1.00 EUR",
                ],
                StockDataKey.SALES.value: ["100 EUR", "200 EUR", "300 EUR"],
                StockDataKey.STOCK_COUNT.value: [100.0, 200.0, 300.0],
            }
        )
        result = calculate_sps(stock_df)
        self.assertEqual(result.to_dict(), expected_result.to_dict())


if __name__ == "__main__":
    main()
