import numpy
from decimal import Decimal


# check if value is number or float and not nan
def is_number_optional_suffix(value) -> bool:
    if isinstance(value, str):
        value = text_to_float(value)

    if value is None:
        return False

    if isinstance(value, Decimal) and value.is_nan():
        return False

    try:
        float_value = float(value)
        if numpy.nan is float_value:
            return False
        return True
    except ValueError:
        return False


# find curr strings: 1000EUR -> EUR
def find_curr(text: str) -> str | None:
    if not isinstance(text, str):
        return None

    curr = [
        "AUD",
        "BRL",
        "CAD",
        "CHF",
        "CNY",
        "CZK",
        "DKK",
        "EUR",
        "GBP",
        "HKD",
        "JPY",
        "KRW",
        "MNT",
        "MXN",
        "NOK",
        "PLN",
        "RUB",
        "THB",
        "TRY",
        "UAH",
        "USD",
        "VND",
    ]
    for c in curr:
        if c in text:
            return c

    return None


# convert text to float: "1,5" => 1.5 "3.5" => 3.5
def text_currency_to_float(text: str) -> float:
    if not isinstance(text, str):
        return text

    t = text
    dot_pos = t.rfind(".")
    comma_pos = t.rfind(",")
    if comma_pos > dot_pos:
        t = t.replace(".", "")
        t = t.replace(",", ".")
    else:
        t = t.replace(",", "")
    return float(t)


# remove currency or % from text: "1,00 EUR" => 1.0
def text_to_float(text: str) -> float | None:
    if text is None:
        return None

    try:
        if not isinstance(text, str):
            return float(text)

        text = text.replace("%", "")
        curr = find_curr(text)
        if curr is not None:
            text = text.replace(curr, "")

        return text_currency_to_float(text.strip())
    except ValueError:
        return None
