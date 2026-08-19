"""CRUD endpoints for Firma (company profile)."""
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from api.database import get_session
from core.models.firma import Firma, FirmaCreate, FirmaRead

router = APIRouter(prefix="/firma", tags=["firma"])


@router.post("/", response_model=FirmaRead, status_code=201)
def opprett_firma(firma_in: FirmaCreate, session: Session = Depends(get_session)) -> Firma:
    firma = Firma.model_validate(firma_in)
    session.add(firma)
    session.commit()
    session.refresh(firma)
    return firma


@router.get("/", response_model=list[FirmaRead])
def hent_alle_firma(session: Session = Depends(get_session)) -> Sequence[Firma]:
    return session.exec(select(Firma)).all()


@router.get("/{firma_id}", response_model=FirmaRead)
def hent_firma(firma_id: int, session: Session = Depends(get_session)) -> Firma:
    firma = session.get(Firma, firma_id)
    if not firma:
        raise HTTPException(status_code=404, detail="Firma ikke funnet")
    return firma


@router.put("/{firma_id}", response_model=FirmaRead)
def oppdater_firma(
    firma_id: int, firma_in: FirmaCreate, session: Session = Depends(get_session)
) -> Firma:
    firma = session.get(Firma, firma_id)
    if not firma:
        raise HTTPException(status_code=404, detail="Firma ikke funnet")
    for field, value in firma_in.model_dump(exclude_unset=True).items():
        setattr(firma, field, value)
    session.add(firma)
    session.commit()
    session.refresh(firma)
    return firma


@router.delete("/{firma_id}", status_code=204)
def slett_firma(firma_id: int, session: Session = Depends(get_session)) -> None:
    firma = session.get(Firma, firma_id)
    if not firma:
        raise HTTPException(status_code=404, detail="Firma ikke funnet")
    session.delete(firma)
    session.commit()
