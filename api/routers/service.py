"""
Serviceinnsikt API endpoints.
POST upload → normalize + analyse
GET analysis
POST freetext question → Claude answer
"""
import json
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, select

from api.database import get_session
from core.agents.serviceinnsikt import serviceinnsikt_agent
from core.connectors.column_mapper import normalize_service_data
from core.connectors.excel_parser import parse_excel_upload
from core.connectors.normalizer import normalize_record
from core.models.firma import Firma
from core.models.service import ServiceOrdre

router = APIRouter(prefix="/firma/{firma_id}/service", tags=["service"])

_analyse_cache: dict[int, dict] = {}


def _require_firma(firma_id: int, session: Session) -> Firma:
    firma = session.get(Firma, firma_id)
    if not firma:
        raise HTTPException(status_code=404, detail="Firma ikke funnet")
    return firma


def _json_default(obj: Any) -> Any:
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"{type(obj)} not serializable")


class SporsmalRequest(BaseModel):
    sporsmal: str


@router.post("/last-opp")
async def last_opp_service(
    firma_id: int,
    fil: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> dict:
    """Upload Excel/CSV with service orders, normalize + analyse."""
    _require_firma(firma_id, session)

    innhold = await fil.read()
    try:
        df = parse_excel_upload(innhold, fil.filename or "upload.xlsx")
        poster = normalize_service_data(df)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    for post in poster:
        normalize_record(post, date_fields=["opprettet", "ferdigstilt"], decimal_fields=[])

    # Replace existing service orders for this firma
    existing = session.exec(select(ServiceOrdre).where(ServiceOrdre.firma_id == firma_id)).all()
    for so in existing:
        session.delete(so)
    session.flush()

    for post in poster:
        so = ServiceOrdre(firma_id=firma_id, **post)
        session.add(so)
    session.commit()

    analyse = serviceinnsikt_agent.analyser(poster)
    _analyse_cache[firma_id] = json.loads(json.dumps(analyse, default=_json_default))

    return {
        "antall_ordre": len(poster),
        "melding": f"Lastet opp og analysert {len(poster)} serviceordrer.",
        "analyse_sammendrag": {
            "antall_forsinkede": analyse["antall_forsinkede"],
            "total_nedetid_timer": analyse["total_nedetid_timer"],
            "gjentakende_feil": len(analyse["gjentakende_feil"]),
        },
    }


@router.get("/analyse")
def hent_analyse(firma_id: int, session: Session = Depends(get_session)) -> dict:
    _require_firma(firma_id, session)
    if firma_id not in _analyse_cache:
        db_poster = session.exec(select(ServiceOrdre).where(ServiceOrdre.firma_id == firma_id)).all()
        if not db_poster:
            return {"melding": "Ingen servicedata lastet opp ennå."}
        poster = [so.model_dump() for so in db_poster]
        analyse = serviceinnsikt_agent.analyser(poster)
        _analyse_cache[firma_id] = json.loads(json.dumps(analyse, default=_json_default))
    return _analyse_cache[firma_id]


@router.post("/sporsmal")
def still_sporsmal(
    firma_id: int,
    req: SporsmalRequest,
    session: Session = Depends(get_session),
) -> dict:
    """AI Q&A — disabled in public demo; requires authentication (Phase 2)."""
    _require_firma(firma_id, session)
    raise HTTPException(
        status_code=403,
        detail="Denne funksjonen krever pålogging — kontakt oss for tilgang.",
    )
