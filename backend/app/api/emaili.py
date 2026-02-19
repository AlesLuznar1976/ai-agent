from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
from sqlalchemy.orm import Session
import json
import os

from app.auth import get_current_user, require_permission
from app.models import (
    TokenData, Permission,
    Email, EmailUpdate, EmailKategorija, RfqPodkategorija, EmailStatus
)
from app.config import get_settings
from app.database import get_db
from app.crud import emaili as crud_emaili
from app.services.email_sync import sync_emails_from_outlook

router = APIRouter()
settings = get_settings()


def db_email_to_response(db_email) -> dict:
    """Pretvori DB email v API response"""
    izvleceni = None
    if db_email.izvleceni_podatki:
        try:
            izvleceni = json.loads(db_email.izvleceni_podatki)
        except (json.JSONDecodeError, TypeError):
            izvleceni = None

    priloge = None
    if db_email.priloge:
        try:
            priloge = json.loads(db_email.priloge)
        except (json.JSONDecodeError, TypeError):
            priloge = None

    analiza_rezultat = None
    if db_email.analiza_rezultat:
        try:
            analiza_rezultat = json.loads(db_email.analiza_rezultat)
        except (json.JSONDecodeError, TypeError):
            analiza_rezultat = None

    return {
        "id": db_email.id,
        "outlook_id": db_email.outlook_id,
        "projekt_id": db_email.projekt_id,
        "zadeva": db_email.zadeva,
        "posiljatelj": db_email.posiljatelj,
        "prejemniki": db_email.prejemniki,
        "telo": db_email.telo,
        "kategorija": db_email.kategorija,
        "rfq_podkategorija": db_email.rfq_podkategorija,
        "status": db_email.status,
        "datum": db_email.datum.isoformat() if db_email.datum else None,
        "izvleceni_podatki": izvleceni,
        "priloge": priloge,
        "analiza_status": db_email.analiza_status,
        "analiza_rezultat": analiza_rezultat,
    }


@router.get("")
async def list_emaili(
    kategorija: Optional[EmailKategorija] = None,
    rfq_podkategorija: Optional[RfqPodkategorija] = None,
    status: Optional[EmailStatus] = None,
    projekt_id: Optional[int] = None,
    current_user: TokenData = Depends(require_permission(Permission.EMAIL_VIEW)),
    db: Session = Depends(get_db),
):
    """Seznam emailov"""

    db_emaili = crud_emaili.list_emaili(
        db,
        kategorija=kategorija.value if kategorija else None,
        status=status.value if status else None,
        projekt_id=projekt_id,
        rfq_podkategorija=rfq_podkategorija.value if rfq_podkategorija else None,
    )

    emaili = [db_email_to_response(e) for e in db_emaili]
    return {"emaili": emaili, "total": len(emaili)}


@router.get("/nekategorizirani")
async def list_nekategorizirani(
    current_user: TokenData = Depends(require_permission(Permission.EMAIL_VIEW)),
    db: Session = Depends(get_db),
):
    """Seznam emailov ki niso dodeljeni projektu"""

    db_emaili = crud_emaili.list_nekategorizirani(db)
    emaili = [db_email_to_response(e) for e in db_emaili]

    return {"emaili": emaili, "total": len(emaili)}


@router.get("/{email_id}")
async def get_email(
    email_id: int,
    current_user: TokenData = Depends(require_permission(Permission.EMAIL_VIEW)),
    db: Session = Depends(get_db),
):
    """Podrobnosti emaila"""

    db_email = crud_emaili.get_email_by_id(db, email_id)
    if not db_email:
        raise HTTPException(status_code=404, detail="Email ne obstaja")

    return db_email_to_response(db_email)


@router.get("/{email_id}/povezani")
async def get_povezani_emaili(
    email_id: int,
    mode: str = "all",
    current_user: TokenData = Depends(require_permission(Permission.EMAIL_VIEW)),
    db: Session = Depends(get_db),
):
    """Vrne povezane emaile - po projektu, pošiljatelju ali niti."""

    db_email = crud_emaili.get_email_by_id(db, email_id)
    if not db_email:
        raise HTTPException(status_code=404, detail="Email ne obstaja")

    related = []
    seen_ids = {email_id}

    # Po projektu
    if mode in ("project", "all") and db_email.projekt_id:
        project_emails = crud_emaili.list_emaili(db, projekt_id=db_email.projekt_id)
        for e in project_emails:
            if e.id not in seen_ids:
                seen_ids.add(e.id)
                r = db_email_to_response(e)
                r["relation"] = "project"
                related.append(r)

    # Po pošiljatelju/domeni
    if mode in ("sender", "all"):
        sender_addr = ""
        if "<" in db_email.posiljatelj and ">" in db_email.posiljatelj:
            sender_addr = db_email.posiljatelj.split("<")[1].split(">")[0]
        if sender_addr and "@" in sender_addr:
            domain = sender_addr.split("@")[1]
            all_emails = crud_emaili.list_emaili(db)
            for e in all_emails:
                if e.id not in seen_ids and domain in (e.posiljatelj or ""):
                    seen_ids.add(e.id)
                    r = db_email_to_response(e)
                    r["relation"] = "sender"
                    related.append(r)

    # Po niti (RE:/FW: matching)
    if mode in ("thread", "all"):
        import re
        clean_subject = re.sub(r"^(RE:|FW:|Fwd:|Re:|Fw:)\s*", "", db_email.zadeva or "", flags=re.IGNORECASE).strip()
        if clean_subject:
            all_emails = crud_emaili.list_emaili(db)
            for e in all_emails:
                if e.id not in seen_ids:
                    e_clean = re.sub(r"^(RE:|FW:|Fwd:|Re:|Fw:)\s*", "", e.zadeva or "", flags=re.IGNORECASE).strip()
                    if e_clean and (e_clean in clean_subject or clean_subject in e_clean):
                        seen_ids.add(e.id)
                        r = db_email_to_response(e)
                        r["relation"] = "thread"
                        related.append(r)

    return {"email_id": email_id, "related": related, "count": len(related)}


@router.get("/{email_id}/attachments/{att_id}")
async def download_attachment(
    email_id: int,
    att_id: str,
    current_user: TokenData = Depends(require_permission(Permission.EMAIL_VIEW)),
    db: Session = Depends(get_db),
):
    """Prenesi prilogo emaila - iz lokalne datoteke ali MS Graph fallback."""

    db_email = crud_emaili.get_email_by_id(db, email_id)
    if not db_email:
        raise HTTPException(status_code=404, detail="Email ne obstaja")

    priloge = []
    if db_email.priloge:
        try:
            priloge = json.loads(db_email.priloge)
        except (json.JSONDecodeError, TypeError):
            priloge = []

    # Poišči prilogo po ID ali indeksu
    attachment = None
    for p in priloge:
        if isinstance(p, dict) and (p.get("id") == att_id or p.get("name") == att_id):
            attachment = p
            break

    # Poskusi po indeksu
    if not attachment:
        try:
            idx = int(att_id)
            if 0 <= idx < len(priloge):
                attachment = priloge[idx]
        except (ValueError, IndexError):
            pass

    if not attachment:
        raise HTTPException(status_code=404, detail="Priloga ne obstaja")

    # Preveri lokalno datoteko
    local_path = attachment.get("local_path")
    if local_path and os.path.exists(local_path):
        return FileResponse(
            local_path,
            filename=attachment.get("name", "attachment"),
            media_type=attachment.get("contentType", "application/octet-stream"),
        )

    # MS Graph fallback
    from app.services.email_sync import get_ms_graph_token
    from app.services.attachment_processor import download_attachment as dl_att

    token = await get_ms_graph_token()
    if not token:
        raise HTTPException(status_code=503, detail="MS Graph ni na voljo")

    graph_att_id = attachment.get("id")
    if not graph_att_id:
        raise HTTPException(status_code=404, detail="Priloga nima Graph ID")

    att_data = await dl_att(token, db_email.outlook_id, graph_att_id)
    if not att_data:
        raise HTTPException(status_code=404, detail="Prenos priloge ni uspel")

    from fastapi.responses import Response
    return Response(
        content=att_data,
        media_type=attachment.get("contentType", "application/octet-stream"),
        headers={"Content-Disposition": f'attachment; filename="{attachment.get("name", "attachment")}"'},
    )


@router.post("/{email_id}/process-attachments")
async def process_email_attachments(
    email_id: int,
    current_user: TokenData = Depends(require_permission(Permission.EMAIL_VIEW)),
    db: Session = Depends(get_db),
):
    """Sproži obdelavo prilog za email."""

    db_email = crud_emaili.get_email_by_id(db, email_id)
    if not db_email:
        raise HTTPException(status_code=404, detail="Email ne obstaja")

    if not db_email.projekt_id:
        raise HTTPException(status_code=400, detail="Email mora biti dodeljen projektu za obdelavo prilog")

    from app.services.attachment_processor import process_email_attachments as proc_att
    result = await proc_att(db, db_email)
    return result


@router.post("/{email_id}/dodeli")
async def dodeli_projektu(
    email_id: int,
    data: EmailUpdate,
    current_user: TokenData = Depends(require_permission(Permission.PROJECT_EDIT)),
    db: Session = Depends(get_db),
):
    """Dodeli email projektu in sproži obdelavo prilog."""

    db_email = crud_emaili.get_email_by_id(db, email_id)
    if not db_email:
        raise HTTPException(status_code=404, detail="Email ne obstaja")

    if data.projekt_id is None:
        raise HTTPException(status_code=400, detail="projekt_id je obvezen")

    db_email = crud_emaili.update_email(
        db, email_id,
        projekt_id=data.projekt_id,
        status="Dodeljen",
    )

    # Avtomatsko sproži obdelavo prilog
    attachment_result = None
    if db_email.priloge:
        try:
            from app.services.attachment_processor import process_email_attachments as proc_att
            attachment_result = await proc_att(db, db_email)
        except Exception as e:
            attachment_result = {"error": str(e)}

    return {
        "message": f"Email dodeljen projektu {data.projekt_id}",
        "email": db_email_to_response(db_email),
        "attachments": attachment_result,
    }


@router.patch("/{email_id}")
async def update_email(
    email_id: int,
    data: EmailUpdate,
    current_user: TokenData = Depends(require_permission(Permission.EMAIL_VIEW)),
    db: Session = Depends(get_db),
):
    """Posodobi email"""

    db_email = crud_emaili.get_email_by_id(db, email_id)
    if not db_email:
        raise HTTPException(status_code=404, detail="Email ne obstaja")

    update_data = data.model_dump(exclude_unset=True)
    # Pretvori enum v string za DB
    if "kategorija" in update_data and update_data["kategorija"]:
        update_data["kategorija"] = update_data["kategorija"].value
    if "status" in update_data and update_data["status"]:
        update_data["status"] = update_data["status"].value
    if "rfq_podkategorija" in update_data and update_data["rfq_podkategorija"]:
        update_data["rfq_podkategorija"] = update_data["rfq_podkategorija"].value

    db_email = crud_emaili.update_email(db, email_id, **update_data)

    return db_email_to_response(db_email)


# ============================================================
# RFQ Deep Analysis
# ============================================================

@router.post("/{email_id}/analyze")
async def analyze_email(
    email_id: int,
    current_user: TokenData = Depends(require_permission(Permission.EMAIL_VIEW)),
    db: Session = Depends(get_db),
):
    """Ročni trigger poglobljene analize RFQ emaila."""

    db_email = crud_emaili.get_email_by_id(db, email_id)
    if not db_email:
        raise HTTPException(status_code=404, detail="Email ne obstaja")

    from app.services.rfq_analyzer import analyze_rfq_email

    try:
        crud_emaili.update_email(db, email_id, analiza_status="Čaka")
        result = await analyze_rfq_email(db, email_id)
        return {
            "message": "Analiza uspešna",
            "email_id": email_id,
            "analiza_status": "Končano",
            "analiza_rezultat": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Napaka pri analizi: {str(e)}")


@router.get("/{email_id}/analysis")
async def get_email_analysis(
    email_id: int,
    current_user: TokenData = Depends(require_permission(Permission.EMAIL_VIEW)),
    db: Session = Depends(get_db),
):
    """Pridobi rezultat poglobljene analize emaila."""

    db_email = crud_emaili.get_email_by_id(db, email_id)
    if not db_email:
        raise HTTPException(status_code=404, detail="Email ne obstaja")

    analiza_rezultat = None
    if db_email.analiza_rezultat:
        try:
            analiza_rezultat = json.loads(db_email.analiza_rezultat)
        except (json.JSONDecodeError, TypeError):
            analiza_rezultat = None

    return {
        "email_id": email_id,
        "analiza_status": db_email.analiza_status,
        "analiza_rezultat": analiza_rezultat,
    }


# ============================================================
# Re-kategorizacija vseh emailov
# ============================================================

@router.post("/recategorize-all")
async def recategorize_all_emails(
    current_user: TokenData = Depends(require_permission(Permission.EMAIL_VIEW)),
    db: Session = Depends(get_db),
):
    """Re-kategoriziraj vse emaile z LLM (Ollama JSON mode)."""
    from app.agents.email_agent import get_email_agent
    from app.services.email_sync import RFQ_ALLOWED_MAILBOXES, EXCLUDED_SENDER_DOMAINS

    email_agent = get_email_agent()
    all_emails = crud_emaili.list_emaili(db)
    updated = 0
    errors = 0

    for db_email in all_emails:
        try:
            # Pripravi attachment names iz prilog
            attachment_names = []
            if db_email.priloge:
                try:
                    priloge = json.loads(db_email.priloge)
                    attachment_names = [p.get("name", "") for p in priloge if isinstance(p, dict)]
                except (json.JSONDecodeError, TypeError):
                    pass

            analysis = await email_agent.categorize_email(
                sender=db_email.posiljatelj or "",
                subject=db_email.zadeva or "",
                body=db_email.telo or "",
                attachments=attachment_names,
            )

            # Ohrani obstoječ mailbox iz izvleceni_podatki
            mailbox = None
            if db_email.izvleceni_podatki:
                try:
                    old_izvl = json.loads(db_email.izvleceni_podatki)
                    mailbox = old_izvl.get("mailbox")
                except (json.JSONDecodeError, TypeError):
                    pass

            # RFQ/Naročilo samo za dovoljene nabiralnike (info, martina, spela)
            if analysis.kategorija in (EmailKategorija.RFQ, EmailKategorija.NAROCILO):
                if not mailbox or mailbox.lower() not in RFQ_ALLOWED_MAILBOXES:
                    analysis = analysis.model_copy(update={
                        "kategorija": EmailKategorija.SPLOSNO,
                        "rfq_podkategorija": None,
                    })

            # Izloči pošiljatelje iz izključenih domen (npr. calcuquote.com)
            if analysis.kategorija in (EmailKategorija.RFQ, EmailKategorija.NAROCILO):
                sender = db_email.posiljatelj or ""
                sender_email = sender.split("<")[-1].replace(">", "").strip() if "<" in sender else sender.strip()
                sender_domain = sender_email.split("@")[-1].lower() if "@" in sender_email else ""
                if sender_domain in EXCLUDED_SENDER_DOMAINS:
                    analysis = analysis.model_copy(update={
                        "kategorija": EmailKategorija.SPLOSNO,
                        "rfq_podkategorija": None,
                    })

            izvleceni = {
                "kategorija": analysis.kategorija.value,
                "zaupanje": analysis.zaupanje,
                "povzetek": analysis.povzetek,
                "predlagan_projekt_id": analysis.predlagan_projekt_id,
                **analysis.izvleceni_podatki,
            }
            if mailbox:
                izvleceni["mailbox"] = mailbox

            update_kwargs = dict(
                kategorija=analysis.kategorija.value,
                izvleceni_podatki=izvleceni,
            )
            if analysis.rfq_podkategorija:
                update_kwargs["rfq_podkategorija"] = analysis.rfq_podkategorija.value
            crud_emaili.update_email(db, db_email.id, **update_kwargs)

            # Počisti pod-kategorijo za ne-RFQ emaile (update_email preskoči None vrednosti)
            if not analysis.rfq_podkategorija and db_email.rfq_podkategorija:
                db_email.rfq_podkategorija = None
                db.commit()

            updated += 1

        except Exception as e:
            print(f"Re-categorize error for email {db_email.id}: {e}")
            errors += 1

    return {
        "message": f"Re-kategoriziranih {updated} emailov, {errors} napak",
        "updated": updated,
        "errors": errors,
        "total": len(all_emails),
    }


# ============================================================
# Sync endpoint - delegira na email_sync servis
# ============================================================

@router.post("/sync")
async def sync_emails(
    current_user: TokenData = Depends(require_permission(Permission.EMAIL_VIEW)),
    db: Session = Depends(get_db),
):
    """Sinhroniziraj emaile iz Outlook preko MS Graph"""
    return await sync_emails_from_outlook(db)


# ============================================================
# Email Send endpoint
# ============================================================

from pydantic import BaseModel


class EmailSendRequest(BaseModel):
    to: str
    subject: str
    body: str
    reply_to_message_id: Optional[str] = None


@router.post("/send")
async def send_email(
    data: EmailSendRequest,
    current_user: TokenData = Depends(require_permission(Permission.EMAIL_SEND)),
    db: Session = Depends(get_db),
):
    """Pošlji email preko MS Graph."""
    from app.services.email_send import send_email_via_graph
    result = await send_email_via_graph(
        to=data.to,
        subject=data.subject,
        body=data.body,
        reply_to_message_id=data.reply_to_message_id,
    )
    return result
