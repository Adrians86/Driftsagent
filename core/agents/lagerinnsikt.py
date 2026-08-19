"""
Lagerinnsikt module agent.
Performs inventory analysis: dead stock, ABC classification, alerts,
predictive restock risk, and AI-slotting recommendations.
Also handles freetext Q&A via Claude API.
"""
import json
from datetime import date
from decimal import Decimal
from typing import Any

from core.agents.base_agent import BaseAgent

LAGERINNSIKT_SYSTEM_PROMPT = """Du er en lageranalytiker som svarer kort og konkret på norsk bokmål.
Du har tilgang til følgende analyserte lagerdata for firmaet:

{analyse_json}

Svar KUN basert på disse dataene. Hvis spørsmålet ikke kan besvares fra
dataene, si det tydelig i stedet for å gjette. Oppgi alltid tall i NOK
med mellomrom som tusenskille (f.eks. "125 000 kr").
"""


def _decimal_default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class LagerinnsiktAgent(BaseAgent):
    module_name = "lagerinnsikt"

    def analyser(self, poster: list[dict], **kwargs) -> dict[str, Any]:
        """
        Run full inventory analysis: dead stock, ABC classification, alerts.
        Returns structured result ready for UI and orchestrator.
        """
        i_dag = date.today()
        dodt_lager: list[dict] = []
        lav_beholdning: list[dict] = []
        overlager: list[dict] = []
        total_verdi = Decimal(0)
        dod_verdi = Decimal(0)

        for post in poster:
            verdi = Decimal(str(post.get("verdi") or 0))
            total_verdi += verdi

            siste = post.get("siste_bevegelse")
            if siste is not None:
                if isinstance(siste, str):
                    from datetime import datetime
                    try:
                        siste = datetime.strptime(siste, "%Y-%m-%d").date()
                    except ValueError:
                        siste = None
                if siste and isinstance(siste, date):
                    dager_siden = (i_dag - siste).days
                    if dager_siden >= 365:
                        dodt_lager.append({**post, "dager_siden_bevegelse": dager_siden})
                        dod_verdi += verdi

            min_niva = post.get("min_niva")
            if min_niva is not None and post["antall"] < min_niva:
                lav_beholdning.append(post)

            maks_niva = post.get("maks_niva")
            if maks_niva is not None and post["antall"] > maks_niva * 1.5:
                overlager.append(post)

        # ABC classification (Pareto on value)
        sortert = sorted(poster, key=lambda p: float(p.get("verdi") or 0), reverse=True)
        kumulativ = Decimal(0)
        for post in sortert:
            kumulativ += Decimal(str(post.get("verdi") or 0))
            andel = kumulativ / total_verdi if total_verdi else Decimal(0)
            if andel <= Decimal("0.80"):
                post["abc_kategori"] = "A"
            elif andel <= Decimal("0.95"):
                post["abc_kategori"] = "B"
            else:
                post["abc_kategori"] = "C"

        prognose = self.prognoser_fremtidig_dodt_lager(poster)
        omplassering = self.foresla_omplassering(poster)

        return {
            "total_verdi": total_verdi,
            "dod_lager_verdi": dod_verdi,
            "dod_lager_antall": len(dodt_lager),
            "dod_lager_poster": sorted(dodt_lager, key=lambda p: float(p.get("verdi") or 0), reverse=True),
            "lav_beholdning": lav_beholdning,
            "overlager": overlager,
            "abc_fordeling": sortert,
            "totalt_antall_poster": len(poster),
            "prognose_dodt_lager": prognose,
            "omplassering_anbefalinger": omplassering,
        }

    @staticmethod
    def prognoser_fremtidig_dodt_lager(poster: list[dict], historikk_maneder: int = 6) -> dict:
        """
        Predictive: flag items moving TOWARD dead stock (falling consumption trend).
        Requires maanedlig_historikk: list[{maned: str, forbruk: float}] per post.
        Returns recommendation only — human-in-the-loop, never automatic action.
        """
        poster_med_historikk = [p for p in poster if p.get("maanedlig_historikk")]
        if not poster_med_historikk:
            return {
                "mangler_historikk": True,
                "risiko_poster": [],
                "antall_i_risikosone": 0,
                "beskjed": "Månedlig forbrukshistorikk ikke tilgjengelig — last opp data med historikkfelt for å aktivere prediksjon.",
            }

        risiko_poster = []
        for post in poster_med_historikk:
            historikk = sorted(post["maanedlig_historikk"], key=lambda h: h.get("maned", ""))
            if len(historikk) < 4:
                continue
            mid = len(historikk) // 2
            forste_halvdel = historikk[:mid]
            andre_halvdel = historikk[mid:]
            snitt_forste = sum(h.get("forbruk", 0) for h in forste_halvdel) / len(forste_halvdel)
            snitt_andre = sum(h.get("forbruk", 0) for h in andre_halvdel) / len(andre_halvdel)

            # Flag if consumption has dropped by >50% and item is not already dead stock
            if snitt_forste > 0 and snitt_andre < snitt_forste * 0.5:
                nedgang_prosent = round((1 - snitt_andre / snitt_forste) * 100, 1)
                risiko_poster.append({
                    **{k: v for k, v in post.items() if k != "maanedlig_historikk"},
                    "snitt_forbruk_forste_halvdel": round(snitt_forste, 2),
                    "snitt_forbruk_andre_halvdel": round(snitt_andre, 2),
                    "nedgang_prosent": nedgang_prosent,
                    "anbefaling": "Vurder reduksjon av lagernivå — forbrukstrend synkende mot null",
                })

        risiko_poster.sort(key=lambda p: p["nedgang_prosent"], reverse=True)
        return {
            "mangler_historikk": False,
            "risiko_poster": risiko_poster,
            "antall_i_risikosone": len(risiko_poster),
        }

    @staticmethod
    def foresla_omplassering(poster: list[dict]) -> list[dict]:
        """
        AI-slotting: rank items by withdrawal frequency for storage placement.
        Uses antall_uttak if available, otherwise falls back to antall as proxy.
        Returns recommendation only — human-in-the-loop, never automatic action.
        """
        har_uttak = any(p.get("antall_uttak") is not None for p in poster)
        sorteringsnokkel = "antall_uttak" if har_uttak else "antall"

        sortert = sorted(poster, key=lambda p: float(p.get(sorteringsnokkel) or 0), reverse=True)
        n = len(sortert)
        grense = max(1, round(n * 0.20))  # top 20% → easy access

        resultat = []
        for i, post in enumerate(sortert):
            resultat.append({
                **{k: v for k, v in post.items()},
                "anbefalt_plassering": "Høy prioritet for lett tilgang" if i < grense else "Kan flyttes",
                "sorteringsgrunnlag": sorteringsnokkel,
            })
        return resultat

    def besvar_sporsmal(self, sporsmal: str, analyse: dict) -> str:
        """Send question + context to Claude API, return answer."""
        import anthropic

        analyse_json = json.dumps(analyse, default=_decimal_default, ensure_ascii=False, indent=2)
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=LAGERINNSIKT_SYSTEM_PROMPT.format(analyse_json=analyse_json),
            messages=[{"role": "user", "content": sporsmal}],
        )
        return response.content[0].text


lagerinnsikt_agent = LagerinnsiktAgent()
