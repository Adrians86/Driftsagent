"""
Driftsagent orchestrator endpoints — cross-domain analysis.
Available only after Lagerinnsikt and Serviceinnsikt have data.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from api.database import get_session
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
    """AI Q&A — disabled in public demo; requires authentication (Phase 2)."""
    firma = session.get(Firma, firma_id)
    if not firma:
        raise HTTPException(status_code=404, detail="Firma ikke funnet")
    raise HTTPException(
        status_code=403,
        detail="Denne funksjonen krever pålogging — kontakt oss for tilgang.",
    )
