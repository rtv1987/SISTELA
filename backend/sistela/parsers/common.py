import re
import unicodedata
from decimal import Decimal


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def compact(value: str) -> str:
    return normalize_text(value).replace(" ", "")


def clean_text(value: str | None) -> str:
    return " ".join((value or "").split())


def parse_decimal(value: str) -> Decimal:
    value = value.strip().replace("\u00a0", " ").replace("\u202f", " ")
    # Only well-formed thousands groups; never interpret model dimensions as quantities.
    if not re.fullmatch(r"[+-]?(?:\d+|\d{1,3}(?: \d{3})+)(?:[.,]\d+)?", value):
        raise ValueError("Invalid decimal quantity")
    return Decimal(value.replace(" ", "").replace(",", "."))


def normalize_unit(value: str) -> str:
    units = {
        "vnt": "vnt.",
        "vnt.": "vnt.",
        "kompl": "kompl.",
        "kompl.": "kompl.",
        "kpl": "kompl.",
        "kpl.": "kompl.",
        "h": "val.",
        "por": "pora",
        "por.": "pora",
        "m": "m",
        "m2": "m2",
        "m3": "m3",
        "kg": "kg",
        "t": "t",
        "100m": "100m",
        "km": "km",
        "val": "val.",
        "val.": "val.",
    }
    key = "".join(unicodedata.normalize("NFKC", value.casefold()).split())
    return units.get(key, clean_text(value))
