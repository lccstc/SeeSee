from __future__ import annotations

import re

from .models import ParsedTransaction


NEGATIVE_CATEGORIES = {
    "rg", "sp", "gs", "xb", "it", "st", "ft", "mx", "gg", "dg", "ae",
    "lulu", "dk", "ebay", "rb", "uber", "xc", "cvs", "ymx", "psn", "chime",
    "ks", "tt", "nike", "nd", "cash", "ps", "ls", "hd",
}
POSITIVE_CATEGORIES = {"rmb"}
ALL_CATEGORIES = NEGATIVE_CATEGORIES | POSITIVE_CATEGORIES

PATTERN1 = re.compile(r"^([+-])(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?\s*(\d+(?:\.\d+)?)?$")
PATTERN2 = re.compile(r"^(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?\s*([+-])(\d+(?:\.\d+)?)?$")
PATTERN3 = re.compile(r"^([a-zA-Z]+)?\s*([+-])(\d+(?:\.\d+)?)\s*(\d+(?:\.\d+)?)?$")
FIXED_CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{5}(?:-[A-Za-z0-9]{5}){2,}$")


def parse_transaction(text: str) -> ParsedTransaction | None:
    trimmed = text.strip()
    if not trimmed:
        return None

    match = PATTERN1.match(trimmed)
    if match:
        sign_str, amount_str, cat_raw, rate_str = match.groups()
        return _parse_match(sign_str, amount_str, cat_raw, rate_str, trimmed)

    match = PATTERN2.match(trimmed)
    if match:
        amount_str, cat_raw, sign_str, rate_str = match.groups()
        return _parse_match(sign_str, amount_str, cat_raw, rate_str, trimmed)

    match = PATTERN3.match(trimmed)
    if match:
        cat_raw, sign_str, amount_str, rate_str = match.groups()
        return _parse_match(sign_str, amount_str, cat_raw, rate_str, trimmed)

    return None


def looks_like_transaction(text: str) -> bool:
    trimmed = text.strip()
    if len(trimmed) < 2:
        return False
    first_token = trimmed.split(None, 1)[0]
    if FIXED_CODE_PATTERN.fullmatch(first_token):
        return False
    return bool(
        trimmed[0] in "+-"
        or re.search(r"\d+[a-zA-Z][+-]", trimmed)
        or re.match(r"^[a-zA-Z]+[+-]\d", trimmed)
    )


def format_confirmation(tx: ParsedTransaction) -> str:
    sign = "+" if tx.rmb_value >= 0 else "-"
    if tx.category == "rmb":
        return f"✅ {sign}{abs(tx.rmb_value):.2f}"
    input_sign = "+" if tx.input_sign > 0 else "-"
    return f"✅ {input_sign}{tx.amount:g} {tx.category.upper()} ×{tx.rate:g} = {sign}{abs(tx.rmb_value):.2f}"


def _parse_match(sign_str: str, amount_str: str, cat_raw: str | None, rate_str: str | None, raw: str) -> ParsedTransaction | None:
    input_sign = 1 if sign_str == "+" else -1
    amount = float(amount_str)
    category = (cat_raw or "rmb").lower()
    rate = float(rate_str) if rate_str else None

    if category not in ALL_CATEGORIES:
        return None

    if category == "rmb":
        if rate is not None:
            return None
        return ParsedTransaction(
            input_sign=input_sign,
            amount=amount,
            category=category,
            rate=None,
            rmb_value=input_sign * amount,
            raw=raw,
        )

    if rate is None or rate <= 0:
        return None

    effective_sign = -input_sign if category in NEGATIVE_CATEGORIES else input_sign
    return ParsedTransaction(
        input_sign=input_sign,
        amount=amount,
        category=category,
        rate=rate,
        rmb_value=effective_sign * amount * rate,
        raw=raw,
    )
