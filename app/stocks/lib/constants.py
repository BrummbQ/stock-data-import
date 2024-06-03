from enum import Enum
from typing import TypedDict
from decimal import Decimal

SYSTEM_PROMPT_TABLES = """
You are stock and finance expert that generates CSV responses

Following tables delimited by xml tags contain columns with financial data. Each table entry has a id and a list of columns. Find for each column a category.
Use this categories, in brackets you see example column names:
Sales (Umsatz, Umsatz in EUR)
SalesPerShare (Umsatz pro Aktie, Umsatz je Aktie)
EquityRatio (Eigenkapitalquote)
MarketCap (Marktkapitalisierung)
EBIT (+Gewinn vor Steuern, EBIT)
TotalDebt (Gesamtverschuldung, Gesamtverbindlichkeiten)
KGV (KGV, Kurs Gewinn Verhältnis)
KBV (Kurs Buchwert Verhältnis)
KUV (Kurs Umsatz Verhältnis)
KCV (Kurs Cashflow Verhältnis)
DividendPerShare (Dividende je Aktie)
DividendYield (Dividendenrendite)
BookPerShare (Buchwert je Aktie)
EarningsPerShare (Ergebnis je Aktie)
CashflowPerShare (Cashflow je Aktie)
StockCount (Anzahl der Aktien)
EmployeeCount (Personal, Mitarbeiter)

Return a CSV with this headers: table;column;category
"""


class StockDataKey(Enum):
    YEAR = "Year"
    BOOK_PER_SHARE = "BookPerShare"
    CASHFLOW_PER_SHARE = "CashflowPerShare"
    DIVIDEND_PER_SHARE = "DividendPerShare"
    DIVIDEND_YIELD = "DividendYield"
    EARNINGS_PER_SHARE = "EarningsPerShare"
    EBIT = "EBIT"
    EMPLOYEE_COUNT = "EmployeeCount"
    EQUITY_RATIO = "EquityRatio"
    KBV = "KBV"
    KCV = "KCV"
    KGV = "KGV"
    KUV = "KUV"
    MARKET_CAP = "MarketCap"
    PRICE_PER_SHARE = "PricePerShare"
    SALES = "Sales"
    SALES_PER_SHARE = "SalesPerShare"
    STOCK_COUNT = "StockCount"
    TOTAL_DEBT = "TotalDebt"


StockMetaFields = Enum(
    "StockMetaFields", ["last_import", "last_story_import", "fnet_estimation_url", "fnet_guv_url"]
)


stock_data_key_map = {
    StockDataKey.SALES.value: ["Umsatzerlöse in Mio.", "Umsatz", "Umsatzerlöse"],
    StockDataKey.EBIT.value: ["EBIT", "EBIT in Mio.", "Ergebnis vor Steuer (EBT)"],
    StockDataKey.SALES_PER_SHARE.value: [
        "Umsatz/Aktie",
        "Umsatz pro Aktie",
        "Umsatz je Aktie",
    ],
    StockDataKey.EARNINGS_PER_SHARE.value: [
        "Ergebnis/Aktie",
        "Ergebnis pro Aktie",
        "Gewinn je Aktie",
        "Ergebnis je Aktie (unverwässert, nach Steuern)",
        "Gewinn je Aktie (unverwässert, nach Steuern)",
    ],
    StockDataKey.BOOK_PER_SHARE.value: [
        "Buchwert/Aktie",
        "Buchwert je Aktie",
        "Buchwert pro Aktie",
    ],
    StockDataKey.CASHFLOW_PER_SHARE.value: [
        "Cashflow/Aktie",
        "Cashflow je Aktie",
        "Cashflow pro Aktie",
    ],
    StockDataKey.DIVIDEND_PER_SHARE.value: ["Dividende", "Dividende je Aktie"],
    StockDataKey.DIVIDEND_YIELD.value: [
        "Dividendenrendite",
        "Dividendenrendite (in %)",
        "Dividendenrendite Jahresende in %",
    ],
    StockDataKey.KGV.value: ["KGV", "Kurs-Gewinn-Verhältnis", "KGV (Jahresendkurs)"],
    StockDataKey.KCV.value: ["KCV", "Kurs-Cashflow-Verhältnis"],
    StockDataKey.KBV.value: ["KBV", "Kurs-Buchwert-Verhältnis"],
    StockDataKey.KUV.value: ["KUV", "Kurs-Umsatz-Verhältnis"],
    StockDataKey.EQUITY_RATIO.value: ["Eigenkapitalquote"],
    StockDataKey.TOTAL_DEBT.value: ["Gesamt­verbindlichkeiten"],
    StockDataKey.MARKET_CAP.value: ["Marktkapitalisierung"],
    StockDataKey.STOCK_COUNT.value: ["Anzahl der Aktien"],
    StockDataKey.EMPLOYEE_COUNT.value: [
        "Anzahl der Mitarbeiter",
        "Personal am Jahresende",
    ],
}

StockStoryItem = TypedDict(
    "StockStoryItem",
    {
        "ISIN": str,
        "source_url": str,
        "published_at": Decimal,
        "fetched_at": Decimal,
        "text_content": str,
        "title": str,
        "data_provider": str,
    },
)

TradingviewStoryItem = TypedDict(
    "TradingviewStoryItem",
    {
        "provider": str,
        "published": int,
        "storyPath": str,
        "title": str,
    },
)
