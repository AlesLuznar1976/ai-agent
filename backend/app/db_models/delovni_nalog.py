"""SQLAlchemy model za ai_agent.DelovniNalogi tabelo"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class DBDelovniNalog(Base):
    __tablename__ = "DelovniNalogi"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    projekt_id = Column(Integer, ForeignKey("ai_agent.Projekti.id"), nullable=False)
    largo_dn_id = Column(Integer, nullable=True)
    stevilka_dn = Column(String(50), nullable=True)
    artikel_id = Column(Integer, nullable=True)
    kolicina = Column(Numeric(18, 4), nullable=True)
    status = Column(String(50), nullable=True)
    datum_plan_zacetek = Column(DateTime, nullable=True)
    datum_plan_konec = Column(DateTime, nullable=True)
    datum_dejanski_zacetek = Column(DateTime, nullable=True)
    datum_dejanski_konec = Column(DateTime, nullable=True)
    zadnja_sinhronizacija = Column(DateTime, default=datetime.now)

    # Relationships
    projekt = relationship("DBProjekt", back_populates="delovni_nalogi")
