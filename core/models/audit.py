from datetime import datetime
from typing import Optional

from sqlmodel import JSON, Column, Field, SQLModel


class DriftsagentSporsmal(SQLModel, table=True):
    """Append-only audit log — never deleted or modified."""
    id: Optional[int] = Field(default=None, primary_key=True)
    firma_id: int = Field(foreign_key="firma.id", index=True)
    sporsmal: str
    involverte_moduler: list[str] = Field(default=[], sa_column=Column(JSON))
    svar: str
    stilt_at: datetime = Field(default_factory=datetime.utcnow)
