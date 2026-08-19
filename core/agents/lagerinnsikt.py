"""
Lagerinnsikt module agent.
Performs inventory analysis: dead stock, ABC classification, alerts.
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

        return {
            "total_verdi": total_verdi,
            "dod_lager_verdi": dod_verdi,
            "dod_lager_antall": len(dodt_lager),
            "dod_lager_poster": sorted(dodt_lager, key=lambda p: float(p.get("verdi") or 0), reverse=True),
            "lav_beholdning": lav_beholdning,
            "overlager": overlager,
            "abc_fordeling": sortert,
            "totalt_antall_poster": len(poster),
        }

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
