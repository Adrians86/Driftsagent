"""
Tests for the LagerinnsiktAgent analysis logic.
Synthetic data only — no real company data.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from core.agents.lagerinnsikt import LagerinnsiktAgent

agent = LagerinnsiktAgent()
TODAY = date.today()


def make_post(artikkelnummer: str, antall: int, verdi: float = 0,
              dager_siden: int | None = None,
              min_niva: int | None = None,
              maks_niva: int | None = None) -> dict:
    siste = (TODAY - timedelta(days=dager_siden)) if dager_siden is not None else None
    return {
        "artikkelnummer": artikkelnummer,
        "beskrivelse": f"Test artikkel {artikkelnummer}",
        "antall": antall,
        "verdi": verdi,
        "siste_bevegelse": siste,
        "min_niva": min_niva,
        "maks_niva": maks_niva,
    }


class TestAnalyserLager:
    def test_empty_inventory(self):
        result = agent.analyser([])
        assert result["total_verdi"] == Decimal(0)
        assert result["dod_lager_antall"] == 0

    def test_dead_stock_detected(self):
        poster = [
            make_post("A1", 10, verdi=1000, dager_siden=400),
            make_post("A2", 5, verdi=500, dager_siden=100),
        ]
        result = agent.analyser(poster)
        assert result["dod_lager_antall"] == 1
        assert result["dod_lager_poster"][0]["artikkelnummer"] == "A1"

    def test_dead_stock_exactly_365_days(self):
        poster = [make_post("A1", 1, verdi=100, dager_siden=365)]
        result = agent.analyser(poster)
        assert result["dod_lager_antall"] == 1

    def test_dead_stock_364_days_not_included(self):
        poster = [make_post("A1", 1, verdi=100, dager_siden=364)]
        result = agent.analyser(poster)
        assert result["dod_lager_antall"] == 0

    def test_lav_beholdning_detected(self):
        poster = [make_post("B1", 3, min_niva=10)]
        result = agent.analyser(poster)
        assert len(result["lav_beholdning"]) == 1

    def test_overlager_detected(self):
        poster = [make_post("C1", 200, maks_niva=100)]
        result = agent.analyser(poster)
        assert len(result["overlager"]) == 1

    def test_overlager_threshold_is_1_5x(self):
        # 150 items, max=100 → 150 > 150: False (exactly 1.5x not over)
        poster = [make_post("C1", 150, maks_niva=100)]
        result = agent.analyser(poster)
        assert len(result["overlager"]) == 0
        # 151 items → over
        poster = [make_post("C2", 151, maks_niva=100)]
        result = agent.analyser(poster)
        assert len(result["overlager"]) == 1

    def test_total_verdi(self):
        poster = [
            make_post("D1", 5, verdi=1000),
            make_post("D2", 3, verdi=2000),
        ]
        result = agent.analyser(poster)
        assert result["total_verdi"] == Decimal("3000")

    def test_abc_klassifisering_a_category(self):
        """Top 80% of value → A"""
        poster = [
            make_post("E1", 1, verdi=8000),
            make_post("E2", 1, verdi=1000),
            make_post("E3", 1, verdi=500),
            make_post("E4", 1, verdi=500),
        ]
        result = agent.analyser(poster)
        abc_map = {p["artikkelnummer"]: p.get("abc_kategori") for p in result["abc_fordeling"]}
        assert abc_map["E1"] == "A"

    def test_no_movement_date_not_counted_as_dead(self):
        """Items without siste_bevegelse should not appear in dead stock."""
        poster = [make_post("F1", 10, dager_siden=None)]
        result = agent.analyser(poster)
        assert result["dod_lager_antall"] == 0

    def test_dead_stock_sorted_by_value_desc(self):
        poster = [
            make_post("G1", 1, verdi=500, dager_siden=400),
            make_post("G2", 1, verdi=5000, dager_siden=400),
            make_post("G3", 1, verdi=1000, dager_siden=400),
        ]
        result = agent.analyser(poster)
        values = [p["verdi"] for p in result["dod_lager_poster"]]
        assert values == sorted(values, reverse=True)
