"""
Tests for the universal ERP connector.
Tests at least 5 different column name variants to verify robust column detection.
Uses only synthetic data — no real company data.
"""
import io
import pytest
import pandas as pd

from core.connectors.excel_parser import detect_column, normalize_lager_data, parse_excel_upload


def make_csv(columns: dict) -> bytes:
    """Build a CSV file from a dict of {column_name: [values]}."""
    df = pd.DataFrame(columns)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def make_excel(columns: dict) -> bytes:
    df = pd.DataFrame(columns)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


# --- detect_column tests (5 variants per field) ---

class TestDetectColumn:
    def _df(self, col_name: str) -> pd.DataFrame:
        return pd.DataFrame({col_name: [1]})

    # artikkelnummer variants
    def test_artikkelnummer_standard(self):
        assert detect_column(self._df("artikkelnummer"), "artikkelnummer") == "artikkelnummer"

    def test_artikkelnummer_varenr(self):
        assert detect_column(self._df("varenr"), "artikkelnummer") == "varenr"

    def test_artikkelnummer_item_number(self):
        assert detect_column(self._df("item_number"), "artikkelnummer") == "item_number"

    def test_artikkelnummer_material(self):
        assert detect_column(self._df("material"), "artikkelnummer") == "material"

    def test_artikkelnummer_artikel(self):
        assert detect_column(self._df("artikkel"), "artikkelnummer") == "artikkel"

    def test_artikkelnummer_art_nr(self):
        assert detect_column(self._df("art_nr"), "artikkelnummer") == "art_nr"

    # antall variants
    def test_antall_saldo(self):
        assert detect_column(self._df("saldo"), "antall") == "saldo"

    def test_antall_quantity(self):
        assert detect_column(self._df("quantity"), "antall") == "quantity"

    def test_antall_qty(self):
        assert detect_column(self._df("qty"), "antall") == "qty"

    def test_antall_stock(self):
        assert detect_column(self._df("stock"), "antall") == "stock"

    def test_antall_lagerbeholdning(self):
        assert detect_column(self._df("lagerbeholdning"), "antall") == "lagerbeholdning"

    # verdi variants
    def test_verdi_lagerverdi(self):
        assert detect_column(self._df("lagerverdi"), "verdi") == "lagerverdi"

    def test_verdi_value(self):
        assert detect_column(self._df("value"), "verdi") == "value"

    def test_verdi_total_value(self):
        assert detect_column(self._df("total_value"), "verdi") == "total_value"

    # Case insensitive
    def test_case_insensitive(self):
        df = pd.DataFrame({"VARENR": [1]})
        assert detect_column(df, "artikkelnummer") == "VARENR"

    # Returns None when no match
    def test_no_match_returns_none(self):
        assert detect_column(pd.DataFrame({"xyz": [1]}), "artikkelnummer") is None


# --- normalize_lager_data tests ---

class TestNormalizeLagerData:
    def _base_data(self, artikkelnummer_col="artikkelnummer", antall_col="antall"):
        return {
            artikkelnummer_col: ["ART-001", "ART-002", "ART-003"],
            antall_col: [10, 0, 50],
            "beskrivelse": ["Bolt M8", "Mutter M8", "Skrue M5"],
            "verdi": [1000.0, 200.0, 500.0],
        }

    def test_standard_columns(self):
        df = pd.DataFrame(self._base_data())
        result = normalize_lager_data(df)
        assert len(result) == 3
        assert result[0]["artikkelnummer"] == "ART-001"
        assert result[0]["antall"] == 10
        assert result[0]["verdi"] == 1000.0

    def test_erp_variant_varenr_saldo(self):
        data = self._base_data("varenr", "saldo")
        df = pd.DataFrame(data)
        result = normalize_lager_data(df)
        assert result[0]["artikkelnummer"] == "ART-001"
        assert result[1]["antall"] == 0

    def test_erp_variant_item_number_qty(self):
        data = self._base_data("item_number", "qty")
        df = pd.DataFrame(data)
        result = normalize_lager_data(df)
        assert result[2]["artikkelnummer"] == "ART-003"

    def test_erp_variant_material_quantity(self):
        data = self._base_data("material", "quantity")
        df = pd.DataFrame(data)
        result = normalize_lager_data(df)
        assert len(result) == 3

    def test_erp_variant_artikkel_stock(self):
        data = self._base_data("artikkel", "stock")
        df = pd.DataFrame(data)
        result = normalize_lager_data(df)
        assert result[0]["antall"] == 10

    def test_raises_on_missing_required_columns(self):
        df = pd.DataFrame({"farge": ["rød", "blå"], "størrelse": [10, 20]})
        with pytest.raises(ValueError, match="obligatoriske kolonner"):
            normalize_lager_data(df)

    def test_optional_columns_default_to_none(self):
        df = pd.DataFrame({
            "artikkelnummer": ["A1"],
            "antall": [5],
        })
        result = normalize_lager_data(df)
        assert result[0]["verdi"] is None
        assert result[0]["siste_bevegelse"] is None
        assert result[0]["min_niva"] is None

    def test_zero_antall_allowed(self):
        df = pd.DataFrame({"artikkelnummer": ["A1"], "antall": [0]})
        result = normalize_lager_data(df)
        assert result[0]["antall"] == 0


# --- parse_excel_upload tests ---

class TestParseExcelUpload:
    def test_parse_csv(self):
        data = {"artikkelnummer": ["A1", "A2"], "antall": [10, 20]}
        csv_bytes = make_csv(data)
        df = parse_excel_upload(csv_bytes, "lager.csv")
        assert list(df.columns) == ["artikkelnummer", "antall"]
        assert len(df) == 2

    def test_parse_excel(self):
        data = {"varenr": ["V1"], "saldo": [99]}
        xls_bytes = make_excel(data)
        df = parse_excel_upload(xls_bytes, "lager.xlsx")
        assert "varenr" in df.columns

    def test_full_erp_export_format_1_standard(self):
        """Simulates a standard Norwegian ERP export."""
        data = {
            "artikkelnummer": ["1001", "1002"],
            "beskrivelse": ["Ventil A", "Pumpe B"],
            "antall": [5, 12],
            "verdi": [2500.0, 18000.0],
            "siste_bevegelse": ["2024-01-15", "2025-06-01"],
        }
        df = pd.DataFrame(data)
        result = normalize_lager_data(df)
        assert result[0]["artikkelnummer"] == "1001"
        assert result[1]["antall"] == 12

    def test_full_erp_export_format_2_english(self):
        """Simulates an English-language ERP export."""
        data = {
            "item_number": ["ITM-01"],
            "description": ["Widget"],
            "quantity": [100],
            "value": [5000.0],
        }
        df = pd.DataFrame(data)
        result = normalize_lager_data(df)
        assert result[0]["artikkelnummer"] == "ITM-01"
        assert result[0]["antall"] == 100

    def test_full_erp_export_format_3_mixed(self):
        """Simulates a mixed Norwegian/English export."""
        data = {
            "material": ["MAT-99"],
            "material_description": ["Gasket"],
            "qty": [7],
            "total_value": [350.0],
            "min_level": [2],
            "max_level": [20],
        }
        df = pd.DataFrame(data)
        result = normalize_lager_data(df)
        assert result[0]["artikkelnummer"] == "MAT-99"
        assert result[0]["min_niva"] == 2
        assert result[0]["maks_niva"] == 20
