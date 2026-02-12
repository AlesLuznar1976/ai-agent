"""CRUD operacije za ChatHistory tabelo"""

from sqlalchemy.orm import Session
from typing import Optional

from app.db_models.chat_history import DBChatMessage


def add_message(
    db: Session,
    user_id: int,
    role: str,
    content: str,
    projekt_id: Optional[int] = None,
    tool_name: Optional[str] = None,
    tool_result: Optional[str] = None,
) -> DBChatMessage:
    """Shrani sporočilo v chat history"""
    msg = DBChatMessage(
        user_id=user_id,
        role=role,
        content=content,
        projekt_id=projekt_id,
        tool_name=tool_name,
        tool_result=tool_result,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_user_history(db: Session, user_id: int, limit: int = 100) -> list[DBChatMessage]:
    """Pridobi zadnjih N sporočil za uporabnika"""
    return (
        db.query(DBChatMessage)
        .filter(DBChatMessage.user_id == user_id)
        .order_by(DBChatMessage.datum.asc())
        .limit(limit)
        .all()
    )


def get_project_history(
    db: Session, user_id: int, projekt_id: int, limit: int = 100
) -> list[DBChatMessage]:
    """Pridobi sporočila za projekt"""
    return (
        db.query(DBChatMessage)
        .filter(
            DBChatMessage.user_id == user_id,
            DBChatMessage.projekt_id == projekt_id,
        )
        .order_by(DBChatMessage.datum.asc())
        .limit(limit)
        .all()
    )


def clear_user_history(db: Session, user_id: int) -> int:
    """Počisti zgodovino za uporabnika. Vrne število izbrisanih."""
    count = (
        db.query(DBChatMessage)
        .filter(DBChatMessage.user_id == user_id)
        .delete()
    )
    db.commit()
    return count
