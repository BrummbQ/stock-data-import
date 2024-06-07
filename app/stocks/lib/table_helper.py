import pandas as pd
from difflib import SequenceMatcher
import csv
import io

from .constants import SimilarityKeyEntry, SimilarityMap, stock_data_key_map


def calculate_similarity(val1, val2) -> float:
    try:
        return SequenceMatcher(None, val1, val2).ratio()
    except Exception:
        # probably type error, doesnt match with anything
        return 0


def find_table_entries(stock_dfs: list[pd.DataFrame]) -> str:
    # calculate similarities for keys
    keys_map: SimilarityMap = {}
    for i, stock_df in enumerate(stock_dfs):
        for row in stock_df[stock_df.columns[0]]:
            for key in stock_data_key_map:
                synonyms = stock_data_key_map[key]
                similarities: list[float] = []
                for s in synonyms:
                    similarities.append(calculate_similarity(row, s))

                similarity_score = max(similarities)
                key_entry: SimilarityKeyEntry = {
                    "table": i,
                    "similarity": similarity_score,
                    "column": row,
                }

                if (
                    key not in keys_map
                    or keys_map[key]["similarity"] < similarity_score
                ) and similarity_score > 0.8:
                    keys_map[key] = key_entry

    # write output csv
    output_csv = io.StringIO()
    writer = csv.writer(output_csv, delimiter=";")
    writer.writerow(["table", "column", "category"])
    for key in keys_map:
        writer.writerow([keys_map[key]["table"], keys_map[key]["column"], key])

    print("Extracted table data:", output_csv.getvalue())
    return output_csv.getvalue()
