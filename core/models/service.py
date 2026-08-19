from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ServiceOrdre(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    firma_id: int = Field(foreign_key="firma.id", index=True)
    ordre_nummer: str
    utstyr_id: str
    opprettet: date
    ferdigstilt: Optional[date] = None
    status: str  # "ÅPEN" | "PÅGÅR" | "FERDIG" | "FORSINKET"
    feilbeskrivelse: Optional[str] = None
    nedetid_timer: Optional[float] = None
    opplastet_at: datetime = Field(default_factory=datetime.utcnow)
