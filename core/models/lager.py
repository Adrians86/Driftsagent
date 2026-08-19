from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class LagerPost(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    firma_id: int = Field(foreign_key="firma.id", index=True)
    artikkelnummer: str
    beskrivelse: str = ""
    antall: int
    verdi: Optional[Decimal] = None
    siste_bevegelse: Optional[date] = None
    min_niva: Optional[int] = None
    maks_niva: Optional[int] = None
    opplastet_at: datetime = Field(default_factory=datetime.utcnow)
