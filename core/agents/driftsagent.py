"""
Driftsagent orchestrator — cross-domain analysis.
Built AFTER Lagerinnsikt and Serviceinnsikt are complete,
because its value comes from connecting domains.
"""
import json
from datetime import date
from decimal import Decimal
from typing import Any

DRIFTSAGENT_SYSTEM_PROMPT = """Du er Driftsagent — en overordnet analytiker som kobler sammen data fra
lager, service, innkjøp og produksjon for å svare på spørsmål som krever
informasjon fra flere områder samtidig.

Tilgjengelige moduldata for dette spørsmålet:
LAGER: {lager_data}
SERVICE: {service_data}

Analyser sammenhenger mellom modulene før du svarer. Vær konkret om
ÅRSAK, ikke bare symptom.
"""


def _json_default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def besvar_tverrfaglig_sporsmal(
    sporsmal: str,
    firma_id: int,
    lager_analyse: dict | None,
    service_analyse: dict | None,
    session,
) -> dict:
    """
    1. Use provided module analyses (caller decides relevance)
    2. Send combined context to Claude for synthesis
    3. Log question + involved modules + answer to DriftsagentSporsmal
    """
    import anthropic
    from core.models.audit import DriftsagentSporsmal

    involverte: list[str] = []
    if lager_analyse:
        involverte.append("lagerinnsikt")
    if service_analyse:
        involverte.append("serviceinnsikt")

    lager_json = json.dumps(lager_analyse or {}, default=_json_default, ensure_ascii=False, indent=2)
    service_json = json.dumps(service_analyse or {}, default=_json_default, ensure_ascii=False, indent=2)

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        system=DRIFTSAGENT_SYSTEM_PROMPT.format(
            lager_data=lager_json,
            service_data=service_json,
        ),
        messages=[{"role": "user", "content": sporsmal}],
    )
    svar = response.content[0].text

    # Append-only audit log
    logg = DriftsagentSporsmal(
        firma_id=firma_id,
        sporsmal=sporsmal,
        involverte_moduler=involverte,
        svar=svar,
    )
    session.add(logg)
    session.commit()
    session.refresh(logg)

    return {
        "svar": svar,
        "involverte_moduler": involverte,
        "logg_id": logg.id,
    }
