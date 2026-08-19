"""
CI isolation test: data between different firma_id is NEVER shared.
All agents and analysis functions must only process data for the requested firma.
Uses synthetic data only.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from core.agents.lagerinnsikt import LagerinnsiktAgent
from core.agents.serviceinnsikt import ServiceinnsiktAgent

TODAY = date.today()


def make_lager_post(artikkelnummer: str, antall: int, verdi: float, firma_id: int) -> dict:
    return {
        "artikkelnummer": artikkelnummer,
        "beskrivelse": f"Artikel {artikkelnummer} for firma {firma_id}",
        "antall": antall,
        "verdi": verdi,
        "firma_id": firma_id,
        "siste_bevegelse": TODAY - timedelta(days=400),
        "min_niva": None,
        "maks_niva": None,
    }


def make_service_ordre(ordre_nummer: str, utstyr_id: str, firma_id: int) -> dict:
    return {
        "ordre_nummer": ordre_nummer,
        "utstyr_id": utstyr_id,
        "opprettet": TODAY - timedelta(days=10),
        "ferdigstilt": None,
        "status": "ÅPEN",
        "feilbeskrivelse": "testfeil",
        "nedetid_timer": 2.0,
        "firma_id": firma_id,
    }


class TestLagerIsolation:
    def test_firma_a_data_does_not_affect_firma_b_result(self):
        """
        Analysing firma A's data and firma B's data separately must yield
        independent results — firma B's analysis does not include firma A's items.
        """
        agent = LagerinnsiktAgent()

        firma_a_data = [
            make_lager_post("A-001", 10, 5000, firma_id=1),
            make_lager_post("A-002", 0, 200, firma_id=1),
        ]
        firma_b_data = [
            make_lager_post("B-001", 5, 1000, firma_id=2),
        ]

        analyse_a = agent.analyser(firma_a_data)
        analyse_b = agent.analyser(firma_b_data)

        # Firma A total
        assert analyse_a["totalt_antall_poster"] == 2
        assert float(analyse_a["total_verdi"]) == 5200.0

        # Firma B total — must not include A's data
        assert analyse_b["totalt_antall_poster"] == 1
        assert float(analyse_b["total_verdi"]) == 1000.0

    def test_dead_stock_isolation(self):
        agent = LagerinnsiktAgent()

        firma_a_data = [make_lager_post("A-DEAD", 10, 9999, firma_id=1)]
        firma_b_data = [make_lager_post("B-ALIVE", 10, 100, firma_id=2)]

        # Give B-ALIVE a recent movement date — not dead
        firma_b_data[0]["siste_bevegelse"] = TODAY - timedelta(days=10)

        analyse_a = agent.analyser(firma_a_data)
        analyse_b = agent.analyser(firma_b_data)

        assert analyse_a["dod_lager_antall"] == 1
        assert analyse_b["dod_lager_antall"] == 0

        # Firma B's dead stock list must be empty — no cross-contamination
        assert len(analyse_b["dod_lager_poster"]) == 0


class TestServiceIsolation:
    def test_firma_service_data_isolated(self):
        agent = ServiceinnsiktAgent()

        firma_a_ordrer = [make_service_ordre("A-ORD-1", "MAS-A", firma_id=1)]
        firma_b_ordrer = [
            make_service_ordre("B-ORD-1", "MAS-B", firma_id=2),
            make_service_ordre("B-ORD-2", "MAS-B", firma_id=2),
        ]

        analyse_a = agent.analyser(firma_a_ordrer)
        analyse_b = agent.analyser(firma_b_ordrer)

        assert analyse_a["totalt_antall_ordre"] == 1
        assert analyse_b["totalt_antall_ordre"] == 2

        # Firma B's equipment frequency must not include A's machine
        utstyr_ids_b = {e["utstyr_id"] for e in analyse_b["hyppigst_service"]}
        assert "MAS-A" not in utstyr_ids_b
        assert "MAS-B" in utstyr_ids_b

    def test_downtime_not_shared(self):
        agent = ServiceinnsiktAgent()

        firma_a = [make_service_ordre("A-O1", "M1", firma_id=1)]
        firma_a[0]["nedetid_timer"] = 100.0
        firma_b = [make_service_ordre("B-O1", "M2", firma_id=2)]
        firma_b[0]["nedetid_timer"] = 5.0

        res_a = agent.analyser(firma_a)
        res_b = agent.analyser(firma_b)

        assert res_a["total_nedetid_timer"] == 100.0
        assert res_b["total_nedetid_timer"] == 5.0
