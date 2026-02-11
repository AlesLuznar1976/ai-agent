"""SQLAlchemy model za ai_agent.CalcuQuoteRFQ tabelo"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class DBCalcuQuoteRFQ(Base):
    __tablename__ = "CalcuQuoteRFQ"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    projekt_id = Column(Integer, ForeignKey("ai_agent.Projekti.id"), nullable=False)
    calcuquote_rfq_id = Column(String(100), nullable=True)
    status = Column(String(50), default="Osnutek")
    datum_vnosa = Column(DateTime, default=datetime.now)
    bom_verzija = Column(Integer, nullable=True)
    cena_ponudbe = Column(Numeric(18, 2), nullable=True)
    datum_ponudbe = Column(DateTime, nullable=True)

    # Relationships
    projekt = relationship("DBProjekt", back_populates="calcuquote_rfqs")
