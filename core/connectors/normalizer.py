"""
Normalizes raw parsed data to internal data model dictionaries
before persistence. Shared utility used by all module connectors.
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def to_date(value: Any) -> date | None:
    """Convert various date representations to a date object."""
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return None


def to_decimal(value: Any) -> Decimal | None:
    """Convert numeric value to Decimal, returning None on failure."""
    if value is None:
        return None
    try:
        return Decimal(str(value).replace(",", ".").replace(" ", ""))
    except InvalidOperation:
        return None


def normalize_record(record: dict, date_fields: list[str], decimal_fields: list[str]) -> dict:
    """Apply type normalization to a single record dict in-place."""
    for field in date_fields:
        if field in record:
            record[field] = to_date(record[field])
    for field in decimal_fields:
        if field in record:
            record[field] = to_decimal(record[field])
    return record
