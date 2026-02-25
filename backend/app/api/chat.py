"""
Chat API - Endpoints za pogovor z AI agentom.

Zgodovina pogovorov in pending actions so shranjeni v SQL Server bazi
(ai_agent.ChatHistory in ai_agent.CakajočeAkcije).
"""

from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from pathlib import Path
import json
import os

from app.auth import get_current_user
from app.models import TokenData
from app.database import get_db
from app.config import get_settings
from app.agents.orchestrator import get_orchestrator
from app.agents.tool_executor import get_tool_executor
from app.crud import chat_history as chat_crud
from app.crud import akcije as akcije_crud

settings = get_settings()

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


@router.post("/with-files")
async def send_message_with_files(
    message: str = Form(""),
    projekt_id: Optional[int] = Form(None),
    files: list[UploadFile] = File([]),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pošlji sporočilo z datotekami - uporabi Claude Opus 4 za analizo."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[WITH-FILES] Received: message='{message[:50]}', files={len(files)}, user={current_user.user_id}")
    print(f"[WITH-FILES] Received: message='{message[:50]}', files={len(files)}, user={current_user.user_id}", flush=True)

    from app.services.file_processor import process_uploaded_file

    # Pripravi upload direktorij
    upload_dir = Path("data/chat_uploads") / str(current_user.user_id) / datetime.now().strftime("%Y%m%d_%H%M%S")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Shrani datoteke in jih procesiraj
    file_infos = []
    attachment_metadata = []

    for upload_file in files:
        # Shrani datoteko
        filename = upload_file.filename or "unknown"
        filepath = upload_dir / filename
        content = await upload_file.read()
        with open(filepath, "wb") as f:
            f.write(content)

        mime_type = upload_file.content_type or "application/octet-stream"

        # Procesiraj za Claude
        file_info = process_uploaded_file(str(filepath), mime_type)
        file_infos.append(file_info)

        # Metadata za frontend
        attachment_metadata.append({
            "filename": filename,
            "size": len(content),
            "mime_type": mime_type,
        })

    # Shrani user sporočilo v DB
    content_for_db = message
    if attachment_metadata:
        filenames = ", ".join(a["filename"] for a in attachment_metadata)
        content_for_db = f"{message}\n[Priložene datoteke: {filenames}]" if message else f"[Priložene datoteke: {filenames}]"

    chat_crud.add_message(
        db,
        user_id=current_user.user_id,
        role="user",
        content=content_for_db,
        projekt_id=projekt_id,
    )

    # Pokliči orchestrator s datotekami
    orchestrator = get_orchestrator()
    agent_response = await orchestrator.process_with_files(
        message=message,
        file_infos=file_infos,
        user_id=current_user.user_id,
        username=current_user.username,
        user_role=getattr(current_user, 'role', 'user'),
        current_project_id=projekt_id,
    )

    # Shrani pending actions v DB (enako kot pri send_message)
    response_actions = []
    if agent_response.needs_confirmation and agent_response.actions:
        for action_data in agent_response.actions:
            db_action = akcije_crud.create_pending_action(
                db,
                user_id=current_user.user_id,
                tip_akcije=action_data.get("tool_name", "unknown"),
                opis=action_data.get("description", ""),
                predlagani_podatki=action_data.get("arguments", {}),
                projekt_id=projekt_id,
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
        projekt_id=projekt_id,
    )

    return {
        "response": agent_response.message,
        "timestamp": datetime.now().isoformat(),
        "attachments": attachment_metadata,
        "suggested_commands": agent_response.suggested_commands,
        "needs_confirmation": len(response_actions) > 0,
        "actions": response_actions if response_actions else None,
        "document_form": agent_response.document_form,
    }


class DocumentFormSubmit(BaseModel):
    doc_type: str
    form_data: dict
    projekt_id: Optional[int] = None


@router.post("/generate-from-form")
async def generate_from_form(
    request: DocumentFormSubmit,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generiraj dokument iz izpolnjene forme — ustvari pending action."""

    # Zberi analizo iz zadnjih chat sporočil (DESC = najnovejša prva)
    from app.db_models.chat_history import DBChatMessage
    recent_messages = (
        db.query(DBChatMessage)
        .filter(DBChatMessage.user_id == current_user.user_id)
        .order_by(DBChatMessage.datum.desc())
        .limit(10)
        .all()
    )
    analysis_parts = []
    for m in recent_messages:
        if m.role == "agent" and len(m.content or "") > 200:
            analysis_parts.append(m.content)

    # Združi analizo + form podatke v content (najnovejša analiza prva)
    content_parts = analysis_parts[:3] if analysis_parts else []
    form_info = "\n\n--- DODATNI PODATKI ---\n"
    for key, value in request.form_data.items():
        if value:
            form_info += f"{key}: {value}\n"
    content_parts.append(form_info)
    content = "\n\n".join(content_parts)

    # Ustvari pending action
    arguments = {
        "doc_type": request.doc_type,
        "content": content,
    }
    if request.projekt_id:
        arguments["projekt_id"] = request.projekt_id

    description = f"Generiraj {request.doc_type} dokument"
    if request.projekt_id:
        description += f" za projekt #{request.projekt_id}"

    db_action = akcije_crud.create_pending_action(
        db,
        user_id=current_user.user_id,
        tip_akcije="generate_document",
        opis=description,
        predlagani_podatki=arguments,
        projekt_id=request.projekt_id,
    )

    # Shrani v chat history
    chat_crud.add_message(
        db,
        user_id=current_user.user_id,
        role="system",
        content=f"[Formular izpolnjen] {description} — čaka potrditev.",
        projekt_id=request.projekt_id,
    )

    return {
        "message": f"{description} — prosim potrdite.",
        "action": {
            "id": f"action_{db_action.id}",
            "description": description,
            "tool_name": "generate_document",
            "status": "Čaka",
        },
    }


class ExportWordRequest(BaseModel):
    content: str
    title: str = "Analiza"


@router.post("/export-word")
async def export_to_word(
    request: ExportWordRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """Pretvori markdown tekst v Word dokument."""
    from app.services.markdown_to_word import markdown_to_docx

    buffer = markdown_to_docx(request.content, title=request.title)

    filename = f"{request.title.replace(' ', '_')}.docx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class GenerateDocumentRequest(BaseModel):
    content: str
    template_type: str  # reklamacija, rfq_analiza, bom_pregled, porocilo


@router.post("/generate-document")
async def generate_document(
    request: GenerateDocumentRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """Generiraj profesionalen Word dokument iz chat analize."""
    import anthropic
    from app.services.document_templates import (
        generate_document as gen_doc,
        DOCUMENT_TYPES,
        EXTRACTION_PROMPTS,
    )

    if request.template_type not in DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Neznan tip predloge: {request.template_type}. Možnosti: {list(DOCUMENT_TYPES.keys())}",
        )

    if not settings.anthropic_api_key:
        raise HTTPException(status_code=500, detail="Anthropic API ključ ni konfiguriran.")

    # Claude ekstrahira strukturirane podatke iz analize
    extraction_prompt = EXTRACTION_PROMPTS[request.template_type]

    try:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"{extraction_prompt}\n\n---\nVSEBINA ZA ANALIZO:\n{request.content}",
            }],
        )

        raw_json = response.content[0].text.strip()

        # Odstrani morebitne markdown code block oznake
        if raw_json.startswith("```"):
            raw_json = raw_json.split("\n", 1)[-1]
        if raw_json.endswith("```"):
            raw_json = raw_json.rsplit("```", 1)[0]
        raw_json = raw_json.strip()

        data = json.loads(raw_json)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Claude ni vrnil veljavnega JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Napaka pri klicu Claude: {str(e)}")

    # Generiraj Word dokument
    buffer = gen_doc(request.template_type, data)

    template_info = DOCUMENT_TYPES[request.template_type]
    filename = f"{template_info['title'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.docx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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

    response_data = {
        "message": result_message,
        "action": _format_action(action),
        "result": result.get("data"),
    }

    # Dodaj download_url za generirane dokumente
    result_data = result.get("data") or {}
    if result_data.get("download_url"):
        response_data["download_url"] = result_data["download_url"]

    return response_data


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
