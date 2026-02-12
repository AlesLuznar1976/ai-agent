"""SQLAlchemy model za ai_agent.ChatHistory tabelo"""

from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class DBChatMessage(Base):
    __tablename__ = "ChatHistory"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ai_agent.Uporabniki.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, agent, system, tool
    content = Column(Text, nullable=True)
    tool_name = Column(String(100), nullable=True)
    tool_result = Column(Text, nullable=True)
    projekt_id = Column(Integer, nullable=True)
    datum = Column(DateTime, default=datetime.now)

    uporabnik = relationship("DBUporabnik")
