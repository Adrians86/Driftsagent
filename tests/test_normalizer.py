"""Tests for the shared normalizer utilities."""
from datetime import date, datetime
from decimal import Decimal

from core.connectors.normalizer import normalize_record, to_date, to_decimal


class TestToDate:
    def test_date_passthrough(self):
        d = date(2024, 6, 15)
        assert to_date(d) == d

    def test_datetime_to_date(self):
        dt = datetime(2024, 6, 15, 12, 0)
        assert to_date(dt) == date(2024, 6, 15)

    def test_iso_string(self):
        assert to_date("2024-06-15") == date(2024, 6, 15)

    def test_norwegian_format(self):
        assert to_date("15.06.2024") == date(2024, 6, 15)

    def test_slash_format(self):
        assert to_date("15/06/2024") == date(2024, 6, 15)

    def test_none_returns_none(self):
        assert to_date(None) is None

    def test_invalid_string_returns_none(self):
        assert to_date("not-a-date") is None


class TestToDecimal:
    def test_float(self):
        assert to_decimal(1234.56) == Decimal("1234.56")

    def test_int(self):
        assert to_decimal(100) == Decimal("100")

    def test_string_with_comma(self):
        assert to_decimal("1 234,50") == Decimal("1234.50")

    def test_none_returns_none(self):
        assert to_decimal(None) is None

    def test_invalid_returns_none(self):
        assert to_decimal("abc") is None


class TestNormalizeRecord:
    def test_date_and_decimal_fields_converted(self):
        record = {
            "artikkelnummer": "A1",
            "siste_bevegelse": "2023-05-10",
            "verdi": "1500.00",
        }
        result = normalize_record(record, date_fields=["siste_bevegelse"], decimal_fields=["verdi"])
        assert result["siste_bevegelse"] == date(2023, 5, 10)
        assert result["verdi"] == Decimal("1500.00")

    def test_missing_fields_not_error(self):
        record = {"artikkelnummer": "A1"}
        result = normalize_record(record, date_fields=["siste_bevegelse"], decimal_fields=["verdi"])
        assert result == {"artikkelnummer": "A1"}
