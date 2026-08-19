from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Firma(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    navn: str
    org_nr: Optional[str] = None
    bransje: Optional[str] = None
    antall_ansatte: Optional[int] = None
    # "Visma" | "24SevenOffice" | "Annet" — descriptive only, never branded
    erp_system: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FirmaCreate(SQLModel):
    navn: str
    org_nr: Optional[str] = None
    bransje: Optional[str] = None
    antall_ansatte: Optional[int] = None
    erp_system: Optional[str] = None


class FirmaRead(SQLModel):
    id: int
    navn: str
    org_nr: Optional[str] = None
    bransje: Optional[str] = None
    antall_ansatte: Optional[int] = None
    erp_system: Optional[str] = None
    created_at: datetime
