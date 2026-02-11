"""
Attachment Processor - prenos, klasifikacija in shranjevanje prilog.

Obdela email priloge iz MS Graph:
- Prenos vsebine (base64 → bytes)
- Klasifikacija po imenu/tipu (BOM, Gerber, PDF, ...)
- Ekstrakcija teksta iz PDF
- Shranjevanje v projektno mapo
- Registracija v DB (ai_agent.Dokumenti)
"""

import os
import base64
import json
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.crud import emaili as crud_emaili, dokumenti as crud_dokumenti

settings = get_settings()

# Bazna pot za dokumente
DOCUMENTS_BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "documents")


# ============================================================
# MS Graph priloge
# ============================================================

async def fetch_attachment_metadata(token: str, message_id: str, mailbox: str = None) -> list[dict]:
    """Pridobi seznam prilog emaila (id, ime, velikost, tip)."""
    mailbox = mailbox or (settings.ms_graph_mailboxes[0] if settings.ms_graph_mailboxes else settings.ms_graph_mailbox)
    url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/messages/{message_id}/attachments"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"$select": "id,name,size,contentType"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json().get("value", [])
    except Exception as e:
        print(f"Napaka pri pridobivanju prilog: {e}")
    return []


async def download_attachment(token: str, message_id: str, attachment_id: str, mailbox: str = None) -> Optional[bytes]:
    """Prenese vsebino priloge iz MS Graph (base64 → bytes)."""
    mailbox = mailbox or (settings.ms_graph_mailboxes[0] if settings.ms_graph_mailboxes else settings.ms_graph_mailbox)
    url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/messages/{message_id}/attachments/{attachment_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                content_bytes = data.get("contentBytes", "")
                if content_bytes:
                    return base64.b64decode(content_bytes)
    except Exception as e:
        print(f"Napaka pri prenosu priloge: {e}")
    return None


# ============================================================
# Klasifikacija prilog
# ============================================================

def classify_attachment(name: str, content_type: str = "") -> str:
    """Klasificiraj prilogo po imenu in tipu.

    Returns:
        Tip dokumenta: BOM, Gerber, Specifikacija, Drugo
    """
    name_lower = name.lower()

    # PDF → preberi tekst
    if name_lower.endswith(".pdf"):
        return "Specifikacija"

    # ZIP/RAR/7Z z "gerber" v imenu
    if any(name_lower.endswith(ext) for ext in [".zip", ".rar", ".7z"]):
        if "gerber" in name_lower:
            return "Gerber"
        return "Drugo"

    # Excel/CSV z "bom" v imenu
    if any(name_lower.endswith(ext) for ext in [".xlsx", ".xls", ".csv"]):
        if "bom" in name_lower:
            return "BOM"
        return "Specifikacija"

    # Word dokumenti
    if any(name_lower.endswith(ext) for ext in [".doc", ".docx"]):
        return "Specifikacija"

    return "Drugo"


# ============================================================
# PDF tekst ekstrakcija
# ============================================================

def extract_pdf_text(pdf_bytes: bytes, max_pages: int = 50, max_chars: int = 20000) -> str:
    """Izvleči tekst iz PDF z PyMuPDF (fitz).

    Args:
        pdf_bytes: PDF vsebina kot bytes
        max_pages: Maksimalno število strani
        max_chars: Maksimalno število znakov

    Returns:
        Čist tekst iz PDF
    """
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []
        total_chars = 0

        for page_num in range(min(len(doc), max_pages)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            text_parts.append(page_text)
            total_chars += len(page_text)
            if total_chars >= max_chars:
                break

        doc.close()

        full_text = "\n".join(text_parts)
        return full_text[:max_chars]

    except Exception as e:
        print(f"PDF ekstrakcija napaka: {e}")
        return ""


# ============================================================
# Shranjevanje v projektno mapo
# ============================================================

def save_attachment_to_project(
    content: bytes,
    filename: str,
    projekt_id: int,
    tip: str,
    db: Session,
    user_id: Optional[int] = None,
) -> dict:
    """Shrani prilogo v projektno mapo in registriraj v DB.

    Args:
        content: Vsebina datoteke
        filename: Ime datoteke
        projekt_id: ID projekta
        tip: Tip dokumenta (BOM, Gerber, ...)
        db: SQLAlchemy session
        user_id: ID uporabnika

    Returns:
        dict z path in dokument ID
    """
    # Ustvari mapo
    project_dir = os.path.join(DOCUMENTS_BASE_PATH, str(projekt_id))
    os.makedirs(project_dir, exist_ok=True)

    # Shrani datoteko
    file_path = os.path.join(project_dir, filename)

    # Če datoteka že obstaja, dodaj suffix
    base, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(file_path):
        file_path = os.path.join(project_dir, f"{base}_{counter}{ext}")
        counter += 1

    with open(file_path, "wb") as f:
        f.write(content)

    # Registriraj v DB
    db_dok = crud_dokumenti.create_dokument(
        db,
        projekt_id=projekt_id,
        naziv_datoteke=filename,
        pot_do_datoteke=file_path,
        tip=tip,
        nalozil_uporabnik=user_id,
    )

    return {
        "dokument_id": db_dok.id,
        "path": file_path,
        "verzija": db_dok.verzija,
    }


# ============================================================
# Celotna obdelava prilog za email
# ============================================================

async def process_email_attachments(db: Session, db_email) -> dict:
    """Obdelaj vse priloge emaila.

    Prenese iz MS Graph, klasificira, shrani v projektno mapo.

    Args:
        db: SQLAlchemy session
        db_email: DBEmail objekt (mora imeti projekt_id)

    Returns:
        dict z rezultati obdelave
    """
    from app.services.email_sync import get_ms_graph_token

    if not db_email.projekt_id:
        return {"error": "Email ni dodeljen projektu", "processed": 0}

    token = await get_ms_graph_token()
    if not token:
        return {"error": "MS Graph ni na voljo", "processed": 0}

    # Ugotovi mailbox iz izvlečenih podatkov
    mailbox = None
    if db_email.izvleceni_podatki:
        try:
            izvl = json.loads(db_email.izvleceni_podatki)
            mailbox = izvl.get("mailbox")
        except (json.JSONDecodeError, TypeError):
            pass

    # Pridobi seznam prilog
    attachments = await fetch_attachment_metadata(token, db_email.outlook_id, mailbox=mailbox)
    if not attachments:
        return {"message": "Email nima prilog", "processed": 0}

    results = []
    updated_priloge = []

    for att in attachments:
        att_id = att.get("id", "")
        att_name = att.get("name", "unknown")
        att_size = att.get("size", 0)
        att_type = att.get("contentType", "")

        # Klasificiraj
        doc_tip = classify_attachment(att_name, att_type)

        # Prenesi
        content = await download_attachment(token, db_email.outlook_id, att_id, mailbox=mailbox)
        if not content:
            updated_priloge.append({
                "id": att_id,
                "name": att_name,
                "size": att_size,
                "contentType": att_type,
                "tip": doc_tip,
                "downloaded": False,
                "error": "Prenos ni uspel",
            })
            continue

        # Shrani v projektno mapo
        save_result = save_attachment_to_project(
            content=content,
            filename=att_name,
            projekt_id=db_email.projekt_id,
            tip=doc_tip,
            db=db,
        )

        # Izvleči tekst iz PDF
        pdf_text = ""
        if att_name.lower().endswith(".pdf"):
            pdf_text = extract_pdf_text(content)

        att_info = {
            "id": att_id,
            "name": att_name,
            "size": att_size,
            "contentType": att_type,
            "tip": doc_tip,
            "downloaded": True,
            "local_path": save_result["path"],
            "dokument_id": save_result["dokument_id"],
            "verzija": save_result["verzija"],
        }
        if pdf_text:
            att_info["pdf_text_preview"] = pdf_text[:500]

        updated_priloge.append(att_info)
        results.append({
            "name": att_name,
            "tip": doc_tip,
            "dokument_id": save_result["dokument_id"],
            "path": save_result["path"],
        })

    # Posodobi priloge v emailu
    crud_emaili.update_email(db, db_email.id, priloge=updated_priloge)

    return {
        "message": f"Obdelano {len(results)} prilog",
        "processed": len(results),
        "attachments": results,
    }
