"""
Lagerinnsikt API endpoints.
POST upload → normalize + analyse
GET analysis, dead stock
POST freetext question → Claude answer
"""
import json
from decimal import Decimal
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, select

from api.database import get_session
from core.agents.lagerinnsikt import lagerinnsikt_agent
from core.connectors.excel_parser import normalize_lager_data, parse_excel_upload
from core.connectors.normalizer import normalize_record
from core.models.audit import DriftsagentSporsmal
from core.models.firma import Firma
from core.models.lager import LagerPost

router = APIRouter(prefix="/firma/{firma_id}/lager", tags=["lager"])

# In-memory cache of last analysis per firma (sufficient for MVP)
_analyse_cache: dict[int, dict] = {}


def _require_firma(firma_id: int, session: Session) -> Firma:
    firma = session.get(Firma, firma_id)
    if not firma:
        raise HTTPException(status_code=404, detail="Firma ikke funnet")
    return firma


def _decimal_default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"{type(obj)} not serializable")


class SporsmalRequest(BaseModel):
    sporsmal: str


@router.post("/last-opp")
async def last_opp_lager(
    firma_id: int,
    fil: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> dict:
    """Upload Excel/CSV, run normalize + analyse, persist to DB."""
    _require_firma(firma_id, session)

    innhold = await fil.read()
    try:
        df = parse_excel_upload(innhold, fil.filename or "upload.xlsx")
        poster = normalize_lager_data(df)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Normalize date/decimal fields
    for post in poster:
        normalize_record(post, date_fields=["siste_bevegelse"], decimal_fields=["verdi"])

    # Clear existing inventory for this firma and persist new data
    existing = session.exec(select(LagerPost).where(LagerPost.firma_id == firma_id)).all()
    for lp in existing:
        session.delete(lp)
    session.flush()

    for post in poster:
        lp = LagerPost(firma_id=firma_id, **post)
        session.add(lp)
    session.commit()

    analyse = lagerinnsikt_agent.analyser(poster)
    _analyse_cache[firma_id] = json.loads(json.dumps(analyse, default=_decimal_default))

    return {
        "antall_poster": len(poster),
        "melding": f"Lastet opp og analysert {len(poster)} lagerposter.",
        "analyse_sammendrag": {
            "total_verdi": float(analyse["total_verdi"]),
            "dod_lager_antall": analyse["dod_lager_antall"],
            "lav_beholdning": len(analyse["lav_beholdning"]),
            "overlager": len(analyse["overlager"]),
        },
    }


@router.get("/analyse")
def hent_analyse(firma_id: int, session: Session = Depends(get_session)) -> dict:
    """Return the latest analysis for this firma."""
    _require_firma(firma_id, session)
    if firma_id not in _analyse_cache:
        # Rebuild from DB
        db_poster = session.exec(select(LagerPost).where(LagerPost.firma_id == firma_id)).all()
        if not db_poster:
            return {"melding": "Ingen lagerdata lastet opp ennå."}
        poster = [lp.model_dump() for lp in db_poster]
        analyse = lagerinnsikt_agent.analyser(poster)
        _analyse_cache[firma_id] = json.loads(json.dumps(analyse, default=_decimal_default))
    return _analyse_cache[firma_id]


@router.get("/dodt-lager")
def hent_dodt_lager(firma_id: int, session: Session = Depends(get_session)) -> dict:
    """Return only dead stock items, sorted by value descending."""
    analyse = hent_analyse(firma_id=firma_id, session=session)
    return {
        "dod_lager_antall": analyse.get("dod_lager_antall", 0),
        "dod_lager_verdi": analyse.get("dod_lager_verdi", 0),
        "poster": analyse.get("dod_lager_poster", []),
    }


@router.post("/sporsmal")
def still_sporsmal(
    firma_id: int,
    req: SporsmalRequest,
    session: Session = Depends(get_session),
) -> dict:
    """Answer a freetext question about the inventory using Claude."""
    _require_firma(firma_id, session)
    analyse = hent_analyse(firma_id=firma_id, session=session)
    if "melding" in analyse and len(analyse) == 1:
        raise HTTPException(status_code=422, detail="Ingen lagerdata å svare på. Last opp data først.")

    svar = lagerinnsikt_agent.besvar_sporsmal(req.sporsmal, analyse)

    # Append-only audit log
    logg = DriftsagentSporsmal(
        firma_id=firma_id,
        sporsmal=req.sporsmal,
        involverte_moduler=["lagerinnsikt"],
        svar=svar,
    )
    session.add(logg)
    session.commit()

    return {"sporsmal": req.sporsmal, "svar": svar}
