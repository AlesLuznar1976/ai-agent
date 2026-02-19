from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DBProjektCasovnica(Base):
    __tablename__ = "ProjektCasovnica"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    projekt_id = Column(Integer, ForeignKey("ai_agent.Projekti.id", ondelete="CASCADE"), nullable=False)
    dogodek = Column(String(100), nullable=False)
    opis = Column(String(500), nullable=True)
    stara_vrednost = Column(String(255), nullable=True)
    nova_vrednost = Column(String(255), nullable=True)
    datum = Column(DateTime, default=datetime.now)
    uporabnik_ali_agent = Column(String(100), nullable=True)

    projekt = relationship("DBProjekt", back_populates="casovnica")
