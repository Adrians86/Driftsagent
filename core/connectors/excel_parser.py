"""
Universal parser for Excel/CSV exports from any ERP system.
Recognizes columns by NAME, not position — robust against different
ERP systems exporting in different column order.
"""
import io
from typing import Optional

import pandas as pd

# Column name variants per field (Norwegian + English, various ERP conventions)
COLUMN_ALIASES: dict[str, list[str]] = {
    "artikkelnummer": ["artikkelnr", "varenr", "artikkel", "item_number", "material", "item_no", "art_nr", "varenum"],
    "beskrivelse": ["varebeskrivelse", "tekst", "description", "material_description", "item_description", "navn"],
    "antall": ["saldo", "lagerbeholdning", "quantity", "stock", "qty", "beholdning", "lager_saldo", "on_hand"],
    "verdi": ["lagerverdi", "value", "total_value", "stock_value", "verdi_nok", "lagerverd"],
    "siste_bevegelse": ["siste_uttak", "last_movement", "last_issue_date", "siste_transaksjon", "last_transaction"],
    "min_niva": ["min", "minimum", "min_level", "reorder_point", "bestillingspunkt", "min_saldo"],
    "maks_niva": ["max", "maximum", "max_level", "maks", "max_saldo"],
}

# Fields required for a valid inventory upload
REQUIRED_FIELDS = ("artikkelnummer", "antall")


def detect_column(df: pd.DataFrame, field: str) -> Optional[str]:
    """Find actual column name in df that matches a known field."""
    aliases = COLUMN_ALIASES.get(field, [field])
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    for alias in [field] + aliases:
        if alias.lower() in df_cols_lower:
            return df_cols_lower[alias.lower()]
    return None


def parse_excel_upload(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Read Excel/CSV bytes, return raw DataFrame."""
    buf = io.BytesIO(file_bytes)
    if filename.lower().endswith(".csv"):
        return pd.read_csv(buf, sep=None, engine="python")
    return pd.read_excel(buf)


def normalize_lager_data(df: pd.DataFrame) -> list[dict]:
    """Map raw DataFrame to internal LagerPost structure."""
    mapping = {f: detect_column(df, f) for f in COLUMN_ALIASES}

    missing = [f for f in REQUIRED_FIELDS if mapping.get(f) is None]
    if missing:
        raise ValueError(
            f"Fant ikke obligatoriske kolonner: {missing}. "
            f"Tilgjengelige kolonner: {list(df.columns)}"
        )

    result = []
    for _, row in df.iterrows():
        artikkelnummer = mapping["artikkelnummer"]
        antall_col = mapping["antall"]
        verdi_col = mapping["verdi"]
        bev_col = mapping["siste_bevegelse"]
        min_col = mapping["min_niva"]
        maks_col = mapping["maks_niva"]
        besk_col = mapping["beskrivelse"]

        result.append({
            "artikkelnummer": str(row[artikkelnummer]).strip(),
            "beskrivelse": str(row[besk_col]).strip() if besk_col and pd.notna(row.get(besk_col)) else "",
            "antall": int(row[antall_col]) if pd.notna(row[antall_col]) else 0,
            "verdi": float(row[verdi_col]) if verdi_col and pd.notna(row.get(verdi_col)) else None,
            "siste_bevegelse": row[bev_col] if bev_col and pd.notna(row.get(bev_col)) else None,
            "min_niva": int(row[min_col]) if min_col and pd.notna(row.get(min_col)) else None,
            "maks_niva": int(row[maks_col]) if maks_col and pd.notna(row.get(maks_col)) else None,
        })
    return result
