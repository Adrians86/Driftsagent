"""
Driftsagent orchestrator endpoints — cross-domain analysis.
Available only after Lagerinnsikt and Serviceinnsikt have data.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from api.database import get_session
from api.routers.lager import hent_analyse as hent_lager_analyse
from api.routers.service import hent_analyse as hent_service_analyse
from core.agents.driftsagent import besvar_tverrfaglig_sporsmal
from core.models.firma import Firma

router = APIRouter(prefix="/firma/{firma_id}/driftsagent", tags=["driftsagent"])


class TverrfagligSporsmalRequest(BaseModel):
    sporsmal: str
    moduler: list[str] = ["lagerinnsikt", "serviceinnsikt"]


@router.post("/sporsmal")
def still_tverrfaglig_sporsmal(
    firma_id: int,
    req: TverrfagligSporsmalRequest,
    session: Session = Depends(get_session),
) -> dict:
    firma = session.get(Firma, firma_id)
    if not firma:
        raise HTTPException(status_code=404, detail="Firma ikke funnet")

    lager_analyse = None
    service_analyse = None

    if "lagerinnsikt" in req.moduler:
        res = hent_lager_analyse(firma_id=firma_id, session=session)
        if "melding" not in res or len(res) > 1:
            lager_analyse = res

    if "serviceinnsikt" in req.moduler:
        res = hent_service_analyse(firma_id=firma_id, session=session)
        if "melding" not in res or len(res) > 1:
            service_analyse = res

    if not lager_analyse and not service_analyse:
        raise HTTPException(
            status_code=422,
            detail="Ingen moduldata tilgjengelig. Last opp lager- og/eller servicedata først.",
        )

    return besvar_tverrfaglig_sporsmal(
        sporsmal=req.sporsmal,
        firma_id=firma_id,
        lager_analyse=lager_analyse,
        service_analyse=service_analyse,
        session=session,
    )
