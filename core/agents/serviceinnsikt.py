"""
Serviceinnsikt module agent.
Analyzes service orders: delays, equipment frequency, downtime, fault patterns.
Also handles freetext Q&A via Claude API.
"""
import json
from collections import Counter, defaultdict
from datetime import date
from typing import Any

from core.agents.base_agent import BaseAgent

SERVICEINNSIKT_SYSTEM_PROMPT = """Du er en serviceanalytiker som svarer kort og konkret på norsk bokmål.
Du har tilgang til følgende analyserte servicedata for firmaet:

{analyse_json}

Svar KUN basert på disse dataene. Hvis spørsmålet ikke kan besvares fra
dataene, si det tydelig i stedet for å gjette. Oppgi alltid tall med
relevante enheter (timer, dager, antall).
"""


def _json_default(obj: Any) -> Any:
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class ServiceinnsiktAgent(BaseAgent):
    module_name = "serviceinnsikt"

    def analyser(self, poster: list[dict], **kwargs) -> dict[str, Any]:
        """
        Analyze service orders:
        - Delayed orders (open > 7 days)
        - Equipment with most frequent service
        - Total downtime per month
        - Fault pattern detection (same fault > 3 times on same equipment)
        """
        i_dag = date.today()
        forsinkede: list[dict] = []
        utstyr_teller: Counter = Counter()
        nedetid_per_maned: dict[str, float] = defaultdict(float)
        feil_per_utstyr: dict[str, list[str]] = defaultdict(list)
        total_nedetid = 0.0

        for ordre in poster:
            opprettet = ordre.get("opprettet")
            if isinstance(opprettet, str):
                from datetime import datetime
                try:
                    opprettet = datetime.strptime(opprettet, "%Y-%m-%d").date()
                except ValueError:
                    opprettet = None

            status = str(ordre.get("status", "")).upper()
            utstyr_id = ordre.get("utstyr_id", "ukjent")

            # Delayed: created > 7 days ago and not FERDIG
            if opprettet and status != "FERDIG":
                dager_siden = (i_dag - opprettet).days
                if dager_siden > 7:
                    forsinkede.append({**ordre, "dager_forsinket": dager_siden})

            # Equipment frequency
            utstyr_teller[utstyr_id] += 1

            # Downtime per month
            nedetid = ordre.get("nedetid_timer") or 0
            total_nedetid += float(nedetid)
            if opprettet:
                maned_key = f"{opprettet.year}-{opprettet.month:02d}"
                nedetid_per_maned[maned_key] += float(nedetid)

            # Fault patterns
            feil = ordre.get("feilbeskrivelse") or ""
            if feil:
                feil_per_utstyr[utstyr_id].append(feil.lower().strip())

        # Pattern detection: same fault text > 3 times on same equipment
        gjentakende_feil = []
        for utstyr_id, feil_liste in feil_per_utstyr.items():
            feil_teller = Counter(feil_liste)
            for feil, antall in feil_teller.items():
                if antall > 3:
                    gjentakende_feil.append({
                        "utstyr_id": utstyr_id,
                        "feilbeskrivelse": feil,
                        "antall_gjentakelser": antall,
                    })

        hyppigst_service = [
            {"utstyr_id": uid, "antall_ordre": count}
            for uid, count in utstyr_teller.most_common(10)
        ]

        forvarslende_monster = self.identifiser_forvarslende_monster(poster)

        return {
            "totalt_antall_ordre": len(poster),
            "antall_forsinkede": len(forsinkede),
            "forsinkede_ordre": sorted(forsinkede, key=lambda o: o.get("dager_forsinket", 0), reverse=True),
            "hyppigst_service": hyppigst_service,
            "total_nedetid_timer": total_nedetid,
            "nedetid_per_maned": dict(sorted(nedetid_per_maned.items())),
            "gjentakende_feil": gjentakende_feil,
            "forvarslende_monster": forvarslende_monster,
        }

    @staticmethod
    def identifiser_forvarslende_monster(ordrer: list[dict]) -> list[dict]:
        """
        Detect escalating fault frequency per equipment.
        Splits each equipment's orders by time (first half vs second half of its date range).
        Flags equipment where second half has >=50% more orders than first half.
        Returns list sorted by escalation ratio descending.
        Returns recommendation only — human-in-the-loop, never automatic action.
        """
        from datetime import datetime

        def parse_dato(verdi):
            if verdi is None:
                return None
            if isinstance(verdi, date):
                return verdi
            try:
                return datetime.strptime(str(verdi), "%Y-%m-%d").date()
            except ValueError:
                return None

        utstyr_ordrer: dict[str, list[date]] = defaultdict(list)
        for ordre in ordrer:
            d = parse_dato(ordre.get("opprettet"))
            if d:
                utstyr_ordrer[ordre.get("utstyr_id", "ukjent")].append(d)

        forvarsel = []
        for utstyr_id, datoer in utstyr_ordrer.items():
            if len(datoer) < 4:
                continue
            datoer_sortert = sorted(datoer)
            tidlig = datoer_sortert[0]
            sent = datoer_sortert[-1]
            midtpunkt = tidlig + (sent - tidlig) / 2
            forste_halvdel = sum(1 for d in datoer_sortert if d <= midtpunkt)
            andre_halvdel = sum(1 for d in datoer_sortert if d > midtpunkt)

            if forste_halvdel == 0:
                continue
            ratio = andre_halvdel / forste_halvdel
            if ratio >= 1.5:
                forvarsel.append({
                    "utstyr_id": utstyr_id,
                    "totalt_antall_ordre": len(datoer),
                    "antall_ordre_forste_halvdel": forste_halvdel,
                    "antall_ordre_andre_halvdel": andre_halvdel,
                    "eskalering_ratio": round(ratio, 2),
                    "anbefaling": "Feilfrekvens eskalerende — vurder forebyggende vedlikehold eller grundig tilstandsanalyse",
                })

        forvarsel.sort(key=lambda e: e["eskalering_ratio"], reverse=True)
        return forvarsel

    def besvar_sporsmal(self, sporsmal: str, analyse: dict) -> str:
        """Send question + context to Claude API, return answer."""
        import anthropic

        analyse_json = json.dumps(analyse, default=_json_default, ensure_ascii=False, indent=2)
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=SERVICEINNSIKT_SYSTEM_PROMPT.format(analyse_json=analyse_json),
            messages=[{"role": "user", "content": sporsmal}],
        )
        return response.content[0].text


serviceinnsikt_agent = ServiceinnsiktAgent()
