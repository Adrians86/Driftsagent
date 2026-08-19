"""
Tests for the ServiceinnsiktAgent analysis logic.
Synthetic data only.
"""
from datetime import date, timedelta

import pytest

from core.agents.serviceinnsikt import ServiceinnsiktAgent

agent = ServiceinnsiktAgent()
TODAY = date.today()


def make_ordre(
    ordre_nummer: str,
    utstyr_id: str,
    dager_siden: int = 1,
    status: str = "ÅPEN",
    feilbeskrivelse: str | None = None,
    nedetid_timer: float | None = None,
) -> dict:
    return {
        "ordre_nummer": ordre_nummer,
        "utstyr_id": utstyr_id,
        "opprettet": TODAY - timedelta(days=dager_siden),
        "ferdigstilt": None,
        "status": status,
        "feilbeskrivelse": feilbeskrivelse,
        "nedetid_timer": nedetid_timer,
    }


class TestAnalyserService:
    def test_empty_returns_zeros(self):
        result = agent.analyser([])
        assert result["totalt_antall_ordre"] == 0
        assert result["antall_forsinkede"] == 0

    def test_forsinket_detected_after_7_days(self):
        ordre = [make_ordre("ORD-1", "MAS-A", dager_siden=8, status="ÅPEN")]
        result = agent.analyser(ordre)
        assert result["antall_forsinkede"] == 1

    def test_not_forsinket_within_7_days(self):
        ordre = [make_ordre("ORD-1", "MAS-A", dager_siden=7, status="ÅPEN")]
        result = agent.analyser(ordre)
        assert result["antall_forsinkede"] == 0

    def test_ferdig_not_counted_as_forsinket(self):
        ordre = [make_ordre("ORD-1", "MAS-A", dager_siden=30, status="FERDIG")]
        result = agent.analyser(ordre)
        assert result["antall_forsinkede"] == 0

    def test_hyppigst_service_correct_order(self):
        ordre = [
            make_ordre("O1", "MAS-B"),
            make_ordre("O2", "MAS-B"),
            make_ordre("O3", "MAS-B"),
            make_ordre("O4", "MAS-A"),
            make_ordre("O5", "MAS-A"),
        ]
        result = agent.analyser(ordre)
        assert result["hyppigst_service"][0]["utstyr_id"] == "MAS-B"
        assert result["hyppigst_service"][0]["antall_ordre"] == 3

    def test_total_nedetid_beregning(self):
        ordre = [
            make_ordre("O1", "M1", nedetid_timer=4.5),
            make_ordre("O2", "M2", nedetid_timer=2.0),
        ]
        result = agent.analyser(ordre)
        assert abs(result["total_nedetid_timer"] - 6.5) < 0.01

    def test_gjentakende_feil_detected_above_3(self):
        ordre = [
            make_ordre("O1", "MAS-X", feilbeskrivelse="oljelek"),
            make_ordre("O2", "MAS-X", feilbeskrivelse="oljelek"),
            make_ordre("O3", "MAS-X", feilbeskrivelse="oljelek"),
            make_ordre("O4", "MAS-X", feilbeskrivelse="oljelek"),
        ]
        result = agent.analyser(ordre)
        assert len(result["gjentakende_feil"]) == 1
        assert result["gjentakende_feil"][0]["antall_gjentakelser"] == 4

    def test_gjentakende_feil_not_detected_at_3_or_below(self):
        ordre = [
            make_ordre("O1", "MAS-Y", feilbeskrivelse="støy"),
            make_ordre("O2", "MAS-Y", feilbeskrivelse="støy"),
            make_ordre("O3", "MAS-Y", feilbeskrivelse="støy"),
        ]
        result = agent.analyser(ordre)
        assert len(result["gjentakende_feil"]) == 0

    def test_nedetid_per_maned_gruppering(self):
        ordre = [
            {
                "ordre_nummer": "O1",
                "utstyr_id": "M1",
                "opprettet": date(2025, 3, 15),
                "status": "FERDIG",
                "nedetid_timer": 3.0,
                "feilbeskrivelse": None,
                "ferdigstilt": date(2025, 3, 20),
            },
            {
                "ordre_nummer": "O2",
                "utstyr_id": "M1",
                "opprettet": date(2025, 3, 22),
                "status": "FERDIG",
                "nedetid_timer": 1.5,
                "feilbeskrivelse": None,
                "ferdigstilt": date(2025, 3, 25),
            },
        ]
        result = agent.analyser(ordre)
        assert "2025-03" in result["nedetid_per_maned"]
        assert abs(result["nedetid_per_maned"]["2025-03"] - 4.5) < 0.01

    def test_forsinkede_sorted_by_dager(self):
        ordre = [
            make_ordre("O1", "M1", dager_siden=10, status="ÅPEN"),
            make_ordre("O2", "M2", dager_siden=30, status="ÅPEN"),
            make_ordre("O3", "M3", dager_siden=15, status="ÅPEN"),
        ]
        result = agent.analyser(ordre)
        dager_list = [o["dager_forsinket"] for o in result["forsinkede_ordre"]]
        assert dager_list == sorted(dager_list, reverse=True)

    def test_analyser_includes_forvarslende_monster_key(self):
        ordre = [make_ordre("O1", "M1")]
        result = agent.analyser(ordre)
        assert "forvarslende_monster" in result


class TestIdentifiserForvarslendeMonstre:
    def _make_ordre_med_dato(self, ordre_nummer: str, utstyr_id: str, dato: date) -> dict:
        return {
            "ordre_nummer": ordre_nummer,
            "utstyr_id": utstyr_id,
            "opprettet": dato,
            "status": "FERDIG",
            "feilbeskrivelse": "testfeil",
            "nedetid_timer": 1.0,
            "ferdigstilt": dato,
        }

    def test_escalating_pattern_detected(self):
        """1 order in first half, 3 in second half → ratio 3.0 ≥ 1.5, flagged."""
        base = date(2025, 1, 1)
        ordrer = [
            self._make_ordre_med_dato("O1", "MAS-A", date(2025, 1, 5)),
            self._make_ordre_med_dato("O2", "MAS-A", date(2025, 7, 1)),
            self._make_ordre_med_dato("O3", "MAS-A", date(2025, 8, 1)),
            self._make_ordre_med_dato("O4", "MAS-A", date(2025, 9, 1)),
        ]
        result = ServiceinnsiktAgent.identifiser_forvarslende_monster(ordrer)
        assert len(result) == 1
        assert result[0]["utstyr_id"] == "MAS-A"
        assert result[0]["eskalering_ratio"] >= 1.5

    def test_stable_pattern_not_flagged(self):
        """2 orders in each half → ratio 1.0, not flagged."""
        ordrer = [
            self._make_ordre_med_dato("O1", "MAS-B", date(2025, 1, 10)),
            self._make_ordre_med_dato("O2", "MAS-B", date(2025, 3, 10)),
            self._make_ordre_med_dato("O3", "MAS-B", date(2025, 7, 10)),
            self._make_ordre_med_dato("O4", "MAS-B", date(2025, 9, 10)),
        ]
        result = ServiceinnsiktAgent.identifiser_forvarslende_monster(ordrer)
        assert all(e["utstyr_id"] != "MAS-B" for e in result)

    def test_decreasing_pattern_not_flagged(self):
        """More orders in first half than second → ratio < 1, not flagged."""
        ordrer = [
            self._make_ordre_med_dato("O1", "MAS-C", date(2025, 1, 5)),
            self._make_ordre_med_dato("O2", "MAS-C", date(2025, 2, 5)),
            self._make_ordre_med_dato("O3", "MAS-C", date(2025, 3, 5)),
            self._make_ordre_med_dato("O4", "MAS-C", date(2025, 9, 5)),
        ]
        result = ServiceinnsiktAgent.identifiser_forvarslende_monster(ordrer)
        assert all(e["utstyr_id"] != "MAS-C" for e in result)

    def test_too_few_orders_skipped(self):
        """Fewer than 4 orders → not enough data for trend, skip."""
        ordrer = [
            self._make_ordre_med_dato("O1", "MAS-D", date(2025, 1, 1)),
            self._make_ordre_med_dato("O2", "MAS-D", date(2025, 6, 1)),
            self._make_ordre_med_dato("O3", "MAS-D", date(2025, 11, 1)),
        ]
        result = ServiceinnsiktAgent.identifiser_forvarslende_monster(ordrer)
        assert len(result) == 0

    def test_sorted_by_escalation_ratio_desc(self):
        """Multiple escalating equipment — highest ratio first."""
        ordrer = [
            # MAS-E: 1 in first half, 4 in second → ratio 4.0
            self._make_ordre_med_dato("E1", "MAS-E", date(2025, 1, 1)),
            self._make_ordre_med_dato("E2", "MAS-E", date(2025, 7, 1)),
            self._make_ordre_med_dato("E3", "MAS-E", date(2025, 8, 1)),
            self._make_ordre_med_dato("E4", "MAS-E", date(2025, 9, 1)),
            self._make_ordre_med_dato("E5", "MAS-E", date(2025, 10, 1)),
            # MAS-F: 2 in first half, 4 in second → ratio 2.0
            self._make_ordre_med_dato("F1", "MAS-F", date(2025, 1, 5)),
            self._make_ordre_med_dato("F2", "MAS-F", date(2025, 2, 5)),
            self._make_ordre_med_dato("F3", "MAS-F", date(2025, 7, 5)),
            self._make_ordre_med_dato("F4", "MAS-F", date(2025, 8, 5)),
            self._make_ordre_med_dato("F5", "MAS-F", date(2025, 9, 5)),
            self._make_ordre_med_dato("F6", "MAS-F", date(2025, 10, 5)),
        ]
        result = ServiceinnsiktAgent.identifiser_forvarslende_monster(ordrer)
        assert len(result) >= 2
        ratios = [e["eskalering_ratio"] for e in result]
        assert ratios == sorted(ratios, reverse=True)
