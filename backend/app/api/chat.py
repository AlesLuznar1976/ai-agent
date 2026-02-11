"""
Chat API - Endpoints za pogovor z AI agentom.

Zgodovina pogovorov je zaenkrat in-memory (TODO: preseliti v bazo).
Pending actions so v memory z dejansko izvedbo ob potrditvi.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.auth import get_current_user
from app.models import TokenData
from app.agents.orchestrator import get_orchestrator
from app.agents.tool_executor import get_tool_executor

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


class PendingActionStore(BaseModel):
    id: str
    tool_name: str
    arguments: dict
    description: str
    user_id: int
    status: str = "Čaka"
    timestamp: str = ""


# In-memory storage (TODO: preseliti v DB)
conversations: dict[int, list[dict]] = {}
pending_actions: dict[str, PendingActionStore] = {}
action_counter = 0


@router.post("", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: TokenData = Depends(get_current_user)
):
    """Pošlji sporočilo agentu"""

    global action_counter

    # Pripravi zgodovino
    if current_user.user_id not in conversations:
        conversations[current_user.user_id] = []

    user_history = conversations[current_user.user_id]

    # Shrani uporabniško sporočilo
    user_history.append({
        "role": "user",
        "content": message.message,
        "timestamp": datetime.now().isoformat(),
        "projekt_id": message.projekt_id
    })

    # Uporabi novi Orchestrator
    orchestrator = get_orchestrator()
    agent_response = await orchestrator.process(
        message=message.message,
        user_id=current_user.user_id,
        username=current_user.username,
        user_role=getattr(current_user, 'role', 'user'),
        current_project_id=message.projekt_id,
        conversation_history=user_history[-20:]  # Zadnjih 20 sporočil
    )

    # Shrani pending actions
    response_actions = []
    if agent_response.needs_confirmation and agent_response.actions:
        for action_data in agent_response.actions:
            action_counter += 1
            action_id = f"action_{action_counter}"

            pending_actions[action_id] = PendingActionStore(
                id=action_id,
                tool_name=action_data.get("tool_name", "unknown"),
                arguments=action_data.get("arguments", {}),
                description=action_data.get("description", ""),
                user_id=current_user.user_id,
                timestamp=datetime.now().isoformat()
            )

            response_actions.append({
                "id": action_id,
                "description": action_data.get("description", ""),
                "tool_name": action_data.get("tool_name", ""),
                "status": "Čaka"
            })

    # Shrani agent odgovor
    user_history.append({
        "role": "agent",
        "content": agent_response.message,
        "timestamp": datetime.now().isoformat()
    })

    return ChatResponse(
        response=agent_response.message,
        timestamp=datetime.now(),
        actions=response_actions if response_actions else None,
        needs_confirmation=len(response_actions) > 0,
        suggested_commands=agent_response.suggested_commands,
        tool_calls=agent_response.tool_calls_made if agent_response.tool_calls_made else None
    )


@router.get("/history")
async def get_full_history(
    current_user: TokenData = Depends(get_current_user)
):
    """Pridobi celotno zgodovino pogovora"""
    user_history = conversations.get(current_user.user_id, [])
    return {"history": user_history}


@router.get("/history/{projekt_id}")
async def get_chat_history(
    projekt_id: int,
    current_user: TokenData = Depends(get_current_user)
):
    """Pridobi zgodovino pogovora za projekt"""
    user_history = conversations.get(current_user.user_id, [])
    project_history = [
        msg for msg in user_history
        if msg.get("projekt_id") == projekt_id
    ]
    return {"history": project_history}


@router.get("/pending-actions")
async def get_pending_actions_list(
    current_user: TokenData = Depends(get_current_user)
):
    """Pridobi čakajoče akcije"""
    pending = [
        a.model_dump() for a in pending_actions.values()
        if a.status == "Čaka" and a.user_id == current_user.user_id
    ]
    return {"actions": pending}


@router.post("/actions/{action_id}/confirm")
async def confirm_action(
    action_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Potrdi in izvedi čakajočo akcijo"""

    action = pending_actions.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Akcija ne obstaja")

    if action.status != "Čaka":
        raise HTTPException(status_code=400, detail="Akcija ni več v čakanju")

    if action.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Ni vaša akcija")

    # Izvedi akcijo preko tool executor-ja
    executor = get_tool_executor()
    result = await executor.execute_confirmed_action(
        tool_name=action.tool_name,
        args=action.arguments,
        user_id=current_user.user_id
    )

    if result.get("success"):
        action.status = "Potrjeno"
        result_message = f"Akcija '{action.description}' uspešno izvedena."
    else:
        action.status = "Napaka"
        result_message = f"Napaka pri izvedbi: {result.get('error', 'Neznana napaka')}"

    # Dodaj v pogovor
    if current_user.user_id in conversations:
        conversations[current_user.user_id].append({
            "role": "system",
            "content": f"[Akcija potrjena] {result_message}",
            "timestamp": datetime.now().isoformat()
        })

    return {
        "message": result_message,
        "action": action.model_dump(),
        "result": result.get("data")
    }


@router.post("/actions/{action_id}/reject")
async def reject_action(
    action_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Zavrni čakajočo akcijo"""

    action = pending_actions.get(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Akcija ne obstaja")

    if action.status != "Čaka":
        raise HTTPException(status_code=400, detail="Akcija ni več v čakanju")

    action.status = "Zavrnjeno"

    if current_user.user_id in conversations:
        conversations[current_user.user_id].append({
            "role": "system",
            "content": f"[Akcija zavrnjena] {action.description}",
            "timestamp": datetime.now().isoformat()
        })

    return {"message": f"Akcija zavrnjena: {action.description}", "action": action.model_dump()}


@router.delete("/history")
async def clear_history(
    current_user: TokenData = Depends(get_current_user)
):
    """Počisti zgodovino pogovora"""
    if current_user.user_id in conversations:
        conversations[current_user.user_id] = []
    return {"message": "Zgodovina počiščena"}
