"""SQLAlchemy model za ai_agent.AuditLog tabelo"""

from sqlalchemy import Column, BigInteger, Integer, String, DateTime, Text
from datetime import datetime

from app.database import Base


class DBAuditLog(Base):
    __tablename__ = "AuditLog"
    __table_args__ = {"schema": "ai_agent"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)  # JSON
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
