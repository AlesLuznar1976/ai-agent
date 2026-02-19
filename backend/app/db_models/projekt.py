from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DBProjekt(Base):
    __tablename__ = "Projekti"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    stevilka_projekta = Column(String(50), unique=True, nullable=False)
    naziv = Column(String(255), nullable=False)
    stranka_id = Column(Integer, nullable=True)
    faza = Column(String(50), nullable=False, default="RFQ")
    status = Column(String(50), nullable=False, default="Aktiven")
    datum_rfq = Column(DateTime, nullable=False, default=datetime.now)
    datum_zakljucka = Column(DateTime, nullable=True)
    odgovorni_prodaja = Column(Integer, ForeignKey("ai_agent.Uporabniki.id"), nullable=True)
    odgovorni_tehnolog = Column(Integer, ForeignKey("ai_agent.Uporabniki.id"), nullable=True)
    opombe = Column(Text, nullable=True)

    prodajalec = relationship("DBUporabnik", foreign_keys=[odgovorni_prodaja], back_populates="projekti_prodaja")
    tehnolog = relationship("DBUporabnik", foreign_keys=[odgovorni_tehnolog], back_populates="projekti_tehnolog")
    dokumenti = relationship("DBDokument", back_populates="projekt", cascade="all, delete-orphan")
    emaili = relationship("DBEmail", back_populates="projekt")
    casovnica = relationship("DBProjektCasovnica", back_populates="projekt", cascade="all, delete-orphan")
    delovni_nalogi = relationship("DBDelovniNalog", back_populates="projekt")
    calcuquote_rfqs = relationship("DBCalcuQuoteRFQ", back_populates="projekt")
    cakajce_akcije = relationship("DBCakajocaAkcija", back_populates="projekt")
    obvestila = relationship("DBObvestilo", back_populates="projekt")
