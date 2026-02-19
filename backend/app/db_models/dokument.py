from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DBDokument(Base):
    __tablename__ = "Dokumenti"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    projekt_id = Column(Integer, ForeignKey("ai_agent.Projekti.id", ondelete="CASCADE"), nullable=False)
    tip = Column(String(50), nullable=False, default="Drugo")
    naziv_datoteke = Column(String(255), nullable=False)
    verzija = Column(Integer, nullable=False, default=1)
    pot_do_datoteke = Column(String(500), nullable=False)
    datum_nalozeno = Column(DateTime, default=datetime.now)
    nalozil_uporabnik = Column(Integer, ForeignKey("ai_agent.Uporabniki.id"), nullable=True)

    projekt = relationship("DBProjekt", back_populates="dokumenti")
    uporabnik = relationship("DBUporabnik")
