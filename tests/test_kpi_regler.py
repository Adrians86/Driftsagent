"""Tests for KPI rule loader."""
from core.rules.loader import load_kpi_regler


class TestKpiRegler:
    def test_loads_all_regler(self):
        regler = load_kpi_regler()
        assert len(regler) >= 3

    def test_each_regel_has_required_fields(self):
        for regel in load_kpi_regler():
            assert "id" in regel
            assert "modul" in regel
            assert "betingelse" in regel
            assert "konsekvens" in regel

    def test_filter_by_modul_lagerinnsikt(self):
        regler = load_kpi_regler(modul="lagerinnsikt")
        assert all(r["modul"] == "lagerinnsikt" for r in regler)
        assert len(regler) >= 3

    def test_filter_by_modul_serviceinnsikt(self):
        regler = load_kpi_regler(modul="serviceinnsikt")
        assert all(r["modul"] == "serviceinnsikt" for r in regler)
        assert len(regler) >= 1

    def test_dodt_lager_regel_present(self):
        regler = load_kpi_regler(modul="lagerinnsikt")
        ids = [r["id"] for r in regler]
        assert "DODT_LAGER" in ids

    def test_forsinket_ordre_regel_present(self):
        regler = load_kpi_regler(modul="serviceinnsikt")
        ids = [r["id"] for r in regler]
        assert "FORSINKET_ORDRE" in ids
