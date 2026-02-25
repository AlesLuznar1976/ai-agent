from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DBCakajocaAkcija(Base):
    __tablename__ = "CakajočeAkcije"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ai_agent.Uporabniki.id"), nullable=True)
    projekt_id = Column(Integer, ForeignKey("ai_agent.Projekti.id"), nullable=True)
    tip_akcije = Column(String(100), nullable=False)
    opis = Column(String(500), nullable=False)
    predlagani_podatki = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="Caka")
    ustvaril_agent = Column(String(100), nullable=True)
    datum_ustvarjeno = Column(DateTime, default=datetime.now)
    potrdil_uporabnik = Column(Integer, ForeignKey("ai_agent.Uporabniki.id"), nullable=True)
    datum_potrjeno = Column(DateTime, nullable=True)
    rezultat = Column(Text, nullable=True)

    projekt = relationship("DBProjekt", back_populates="cakajce_akcije")
    uporabnik = relationship("DBUporabnik", foreign_keys=[potrdil_uporabnik])
