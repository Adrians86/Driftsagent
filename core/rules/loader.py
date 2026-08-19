"""Loads KPI rules from YAML — single source of truth for all thresholds."""
import os
from pathlib import Path
from typing import Any

import yaml

_DATA_DIR = Path(__file__).parent / "data"


def load_kpi_regler(modul: str | None = None) -> list[dict[str, Any]]:
    """Return KPI rules, optionally filtered by module name."""
    path = _DATA_DIR / "kpi_definisjoner.yaml"
    with open(path, encoding="utf-8") as f:
        regler: list[dict] = yaml.safe_load(f)
    if modul:
        return [r for r in regler if r.get("modul") == modul]
    return regler
