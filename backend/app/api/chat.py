"""
Chat API - Endpoints za pogovor z AI agentom.

Zgodovina pogovorov in pending actions so shranjeni v SQL Server bazi
(ai_agent.ChatHistory in ai_agent.CakajočeAkcije).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
import json

from app.auth import get_current_user
from app.models import TokenData
from app.database import get_db
from app.agents.orchestrator import get_orchestrator
from app.agents.tool_executor import get_tool_executor
from app.crud import chat_history as chat_crud
from app.crud import akcije as akcije_crud

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    projekt_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    timestamp: datetime
    actions: Optional[list[dict]] = None
    needs_confirmation: bool = False
    suggested_commands: Optional[list[str]] = None
    tool_calls: Optional[list[dict]] = None


def _format_history_message(msg) -> dict:
    """Pretvori DB sporočilo v API format"""
    return {
        "role": msg.role,
        "content": msg.content,
        "timestamp": msg.datum.isoformat() if msg.datum else None,
        "projekt_id": msg.projekt_id,
    }


def _format_action(akcija) -> dict:
    """Pretvori DB akcijo v API format"""
    arguments = {}
    if akcija.predlagani_podatki:
        try:
            arguments = json.loads(akcija.predlagani_podatki)
        except (json.JSONDecodeError, TypeError):
            arguments = {}

    return {
        "id": f"action_{akcija.id}",
        "tool_name": akcija.tip_akcije,
        "arguments": arguments,
        "description": akcija.opis,
        "user_id": akcija.user_id,
        "status": akcija.status,
        "timestamp": akcija.datum_ustvarjeno.isoformat() if akcija.datum_ustvarjeno else "",
    }


def _parse_action_id(action_id: str) -> int:
    """Pretvori 'action_123' v int 123"""
    if action_id.startswith("action_"):
        try:
            return int(action_id[7:])
        except ValueError:
            pass
    raise HTTPException(status_code=400, detail=f"Neveljaven ID akcije: {action_id}")


@router.post("", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pošlji sporočilo agentu"""

    # Shrani uporabniško sporočilo v DB
    chat_crud.add_message(
        db,
        user_id=current_user.user_id,
        role="user",
        content=message.message,
        projekt_id=message.projekt_id,
    )

    # Pripravi zgodovino iz DB za orchestrator
    db_history = chat_crud.get_user_history(db, current_user.user_id, limit=20)
    conversation_history = [_format_history_message(m) for m in db_history]

    # Uporabi Orchestrator
    orchestrator = get_orchestrator()
    agent_response = await orchestrator.process(
        message=message.message,
        user_id=current_user.user_id,
        username=current_user.username,
        user_role=getattr(current_user, 'role', 'user'),
        current_project_id=message.projekt_id,
        conversation_history=conversation_history[-20:],
    )

    # Shrani pending actions v DB
    response_actions = []
    if agent_response.needs_confirmation and agent_response.actions:
        for action_data in agent_response.actions:
            db_action = akcije_crud.create_pending_action(
                db,
                user_id=current_user.user_id,
                tip_akcije=action_data.get("tool_name", "unknown"),
                opis=action_data.get("description", ""),
                predlagani_podatki=action_data.get("arguments", {}),
                projekt_id=message.projekt_id,
            )

            response_actions.append({
                "id": f"action_{db_action.id}",
                "description": action_data.get("description", ""),
                "tool_name": action_data.get("tool_name", ""),
                "status": "Čaka",
            })

    # Shrani agent odgovor v DB
    chat_crud.add_message(
        db,
        user_id=current_user.user_id,
        role="agent",
        content=agent_response.message,
        projekt_id=message.projekt_id,
    )

    return ChatResponse(
        response=agent_response.message,
        timestamp=datetime.now(),
        actions=response_actions if response_actions else None,
        needs_confirmation=len(response_actions) > 0,
        suggested_commands=agent_response.suggested_commands,
        tool_calls=agent_response.tool_calls_made if agent_response.tool_calls_made else None,
    )


@router.get("/history")
async def get_full_history(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pridobi celotno zgodovino pogovora"""
    messages = chat_crud.get_user_history(db, current_user.user_id)
    return {"history": [_format_history_message(m) for m in messages]}


@router.get("/history/{projekt_id}")
async def get_chat_history(
    projekt_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pridobi zgodovino pogovora za projekt"""
    messages = chat_crud.get_project_history(db, current_user.user_id, projekt_id)
    return {"history": [_format_history_message(m) for m in messages]}


@router.get("/pending-actions")
async def get_pending_actions_list(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pridobi čakajoče akcije"""
    actions = akcije_crud.list_pending_actions(db, current_user.user_id)
    return {"actions": [_format_action(a) for a in actions]}


@router.post("/actions/{action_id}/confirm")
async def confirm_action(
    action_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Potrdi in izvedi čakajočo akcijo"""

    db_id = _parse_action_id(action_id)
    action = akcije_crud.get_pending_action(db, db_id)
    if not action:
        raise HTTPException(status_code=404, detail="Akcija ne obstaja")

    if action.status != "Čaka":
        raise HTTPException(status_code=400, detail="Akcija ni več v čakanju")

    if action.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Ni vaša akcija")

    # Pripravi argumente
    arguments = {}
    if action.predlagani_podatki:
        try:
            arguments = json.loads(action.predlagani_podatki)
        except (json.JSONDecodeError, TypeError):
            arguments = {}

    # Izvedi akcijo preko tool executor-ja
    executor = get_tool_executor()
    result = await executor.execute_confirmed_action(
        tool_name=action.tip_akcije,
        args=arguments,
        user_id=current_user.user_id,
    )

    if result.get("success"):
        akcije_crud.confirm_action(
            db, db_id, current_user.user_id,
            rezultat=json.dumps(result.get("data")),
        )
        result_message = f"Akcija '{action.opis}' uspešno izvedena."
    else:
        akcije_crud.fail_action(db, db_id, result.get("error", "Neznana napaka"))
        result_message = f"Napaka pri izvedbi: {result.get('error', 'Neznana napaka')}"

    # Dodaj v chat history
    chat_crud.add_message(
        db,
        user_id=current_user.user_id,
        role="system",
        content=f"[Akcija potrjena] {result_message}",
    )

    return {
        "message": result_message,
        "action": _format_action(action),
        "result": result.get("data"),
    }


@router.post("/actions/{action_id}/reject")
async def reject_action(
    action_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Zavrni čakajočo akcijo"""

    db_id = _parse_action_id(action_id)
    action = akcije_crud.get_pending_action(db, db_id)
    if not action:
        raise HTTPException(status_code=404, detail="Akcija ne obstaja")

    if action.status != "Čaka":
        raise HTTPException(status_code=400, detail="Akcija ni več v čakanju")

    akcije_crud.reject_action(db, db_id)

    # Dodaj v chat history
    chat_crud.add_message(
        db,
        user_id=current_user.user_id,
        role="system",
        content=f"[Akcija zavrnjena] {action.opis}",
    )

    return {
        "message": f"Akcija zavrnjena: {action.opis}",
        "action": _format_action(action),
    }


@router.delete("/history")
async def clear_history(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Počisti zgodovino pogovora"""
    chat_crud.clear_user_history(db, current_user.user_id)
    return {"message": "Zgodovina počiščena"}
