from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class InnkjopsOrdre(SQLModel, table=True):
    """Procurement order — placeholder for future brief."""
    id: Optional[int] = Field(default=None, primary_key=True)
    firma_id: int = Field(foreign_key="firma.id", index=True)
    ordre_nummer: str
    leverandor: Optional[str] = None
    artikkelnummer: Optional[str] = None
    beskrivelse: Optional[str] = None
    bestilt_antall: int = 0
    mottatt_antall: int = 0
    enhetspris: Optional[Decimal] = None
    bestilt_dato: Optional[date] = None
    forventet_levering: Optional[date] = None
    status: str = "ÅPEN"
    opplastet_at: datetime = Field(default_factory=datetime.utcnow)
