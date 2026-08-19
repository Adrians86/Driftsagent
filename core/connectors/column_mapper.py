"""
Flexible column recognition for service order uploads.
Mirrors the approach in excel_parser.py but for ServiceOrdre fields.
"""
from typing import Optional

import pandas as pd

SERVICE_COLUMN_ALIASES: dict[str, list[str]] = {
    "ordre_nummer": ["ordrenr", "order_number", "order_no", "ordre_id", "work_order", "wo_number"],
    "utstyr_id": ["utstyr", "equipment_id", "machine_id", "maskin_id", "asset_id", "utstyr_nr"],
    "opprettet": ["opprettet_dato", "created", "created_date", "dato_opprettet", "open_date", "åpnet"],
    "ferdigstilt": ["ferdig_dato", "completed", "completed_date", "close_date", "lukket_dato"],
    "status": ["ordre_status", "order_status", "tilstand", "state"],
    "feilbeskrivelse": ["feil", "problem", "fault_description", "symptom", "beskrivelse", "description"],
    "nedetid_timer": ["nedetid", "downtime", "downtime_hours", "timer_nede", "hours_down"],
}

SERVICE_REQUIRED_FIELDS = ("ordre_nummer", "utstyr_id", "opprettet", "status")


def detect_service_column(df: pd.DataFrame, field: str) -> Optional[str]:
    """Find actual column name in df that matches a known service order field."""
    aliases = SERVICE_COLUMN_ALIASES.get(field, [field])
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    for alias in [field] + aliases:
        if alias.lower() in df_cols_lower:
            return df_cols_lower[alias.lower()]
    return None


def normalize_service_data(df: pd.DataFrame) -> list[dict]:
    """Map raw DataFrame to internal ServiceOrdre structure."""
    mapping = {f: detect_service_column(df, f) for f in SERVICE_COLUMN_ALIASES}

    missing = [f for f in SERVICE_REQUIRED_FIELDS if mapping.get(f) is None]
    if missing:
        raise ValueError(
            f"Fant ikke obligatoriske kolonner: {missing}. "
            f"Tilgjengelige kolonner: {list(df.columns)}"
        )

    result = []
    for _, row in df.iterrows():
        result.append({
            "ordre_nummer": str(row[mapping["ordre_nummer"]]).strip(),
            "utstyr_id": str(row[mapping["utstyr_id"]]).strip(),
            "opprettet": row[mapping["opprettet"]],
            "ferdigstilt": row.get(mapping["ferdigstilt"]) if mapping["ferdigstilt"] else None,
            "status": str(row[mapping["status"]]).strip().upper(),
            "feilbeskrivelse": str(row[mapping["feilbeskrivelse"]]).strip()
            if mapping["feilbeskrivelse"] and pd.notna(row.get(mapping["feilbeskrivelse"]))
            else None,
            "nedetid_timer": float(row[mapping["nedetid_timer"]])
            if mapping["nedetid_timer"] and pd.notna(row.get(mapping["nedetid_timer"]))
            else None,
        })
    return result
