from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
import json
import httpx

from app.auth import get_current_user, require_permission
from app.models import (
    TokenData, Permission,
    Email, EmailUpdate, EmailKategorija, EmailStatus
)
from app.config import get_settings
from app.database import get_db
from app.crud import emaili as crud_emaili

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

    return {
        "id": db_email.id,
        "outlook_id": db_email.outlook_id,
        "projekt_id": db_email.projekt_id,
        "zadeva": db_email.zadeva,
        "posiljatelj": db_email.posiljatelj,
        "prejemniki": db_email.prejemniki,
        "telo": db_email.telo,
        "kategorija": db_email.kategorija,
        "status": db_email.status,
        "datum": db_email.datum.isoformat() if db_email.datum else None,
        "izvleceni_podatki": izvleceni,
        "priloge": priloge,
    }


@router.get("")
async def list_emaili(
    kategorija: Optional[EmailKategorija] = None,
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


@router.post("/{email_id}/dodeli")
async def dodeli_projektu(
    email_id: int,
    data: EmailUpdate,
    current_user: TokenData = Depends(require_permission(Permission.PROJECT_EDIT)),
    db: Session = Depends(get_db),
):
    """Dodeli email projektu"""

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

    return {
        "message": f"Email dodeljen projektu {data.projekt_id}",
        "email": db_email_to_response(db_email),
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

    db_email = crud_emaili.update_email(db, email_id, **update_data)

    return db_email_to_response(db_email)


# ============================================================
# MS Graph Email Sync
# ============================================================

async def get_ms_graph_token() -> Optional[str]:
    """Pridobi MS Graph access token"""
    if not all([settings.ms_graph_client_id, settings.ms_graph_client_secret, settings.ms_graph_tenant_id]):
        return None

    url = f"https://login.microsoftonline.com/{settings.ms_graph_tenant_id}/oauth2/v2.0/token"
    data = {
        "client_id": settings.ms_graph_client_id,
        "client_secret": settings.ms_graph_client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        if response.status_code == 200:
            return response.json().get("access_token")
    return None


async def fetch_emails_from_graph(token: str, top: int = 20) -> list[dict]:
    """Pridobi zadnje emaile iz MS Graph"""
    mailbox = settings.ms_graph_mailbox
    url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/messages"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "$top": top,
        "$orderby": "receivedDateTime desc",
        "$select": "id,subject,from,toRecipients,body,receivedDateTime,hasAttachments",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get("value", [])
    return []


async def categorize_email_with_llm(zadeva: str, telo: str) -> dict:
    """Kategoriziraj email z LLM (Ollama)"""
    try:
        prompt = f"""Analiziraj naslednji email in ga kategoriziraj.

Zadeva: {zadeva}
Telo (prvih 500 znakov): {telo[:500] if telo else 'Prazno'}

Vrni SAMO eno od naslednjih kategorij:
- RFQ (povpraševanje za ponudbo)
- Naročilo (potrditev naročila)
- Sprememba (sprememba specifikacij/datotek)
- Dokumentacija (pošiljanje dokumentov)
- Reklamacija (pritožba/reklamacija)
- Splošno (drugo)

Kategorija:"""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            if response.status_code == 200:
                result = response.json().get("response", "").strip()
                # Izvleci kategorijo iz odgovora
                kategorije = ["RFQ", "Naročilo", "Sprememba", "Dokumentacija", "Reklamacija", "Splošno"]
                for kat in kategorije:
                    if kat.lower() in result.lower():
                        return {"kategorija": kat, "ai_response": result}
    except Exception as e:
        print(f"LLM categorizacija napaka: {e}")

    return {"kategorija": "Splošno", "ai_response": None}


@router.post("/sync")
async def sync_emails(
    current_user: TokenData = Depends(require_permission(Permission.EMAIL_VIEW)),
    db: Session = Depends(get_db),
):
    """Sinhroniziraj emaile iz Outlook preko MS Graph"""

    token = await get_ms_graph_token()
    if not token:
        return {
            "message": "Email sinhronizacija ni na voljo - potrebna MS Graph konfiguracija",
            "synced": 0,
            "new_emails": [],
        }

    graph_emails = await fetch_emails_from_graph(token)
    new_emails = []

    for msg in graph_emails:
        outlook_id = msg.get("id", "")

        # Preskoči če že obstaja
        existing = crud_emaili.get_email_by_outlook_id(db, outlook_id)
        if existing:
            continue

        zadeva = msg.get("subject", "Brez zadeve")
        from_data = msg.get("from", {}).get("emailAddress", {})
        posiljatelj = f"{from_data.get('name', '')} <{from_data.get('address', '')}>"
        prejemniki_list = msg.get("toRecipients", [])
        prejemniki = ", ".join(
            r.get("emailAddress", {}).get("address", "") for r in prejemniki_list
        )
        telo = msg.get("body", {}).get("content", "")
        datum_str = msg.get("receivedDateTime", "")

        try:
            datum = datetime.fromisoformat(datum_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            datum = datetime.now()

        # AI kategorizacija
        ai_result = await categorize_email_with_llm(zadeva, telo)
        kategorija = ai_result["kategorija"]

        # Shrani v bazo
        db_email = crud_emaili.create_email(
            db,
            outlook_id=outlook_id,
            zadeva=zadeva,
            posiljatelj=posiljatelj,
            prejemniki=prejemniki,
            telo=telo[:4000],  # Omejitev za NVARCHAR(MAX) performance
            kategorija=kategorija,
            datum=datum,
            izvleceni_podatki={"ai_kategorija": kategorija, "ai_response": ai_result.get("ai_response")},
        )

        new_emails.append(db_email_to_response(db_email))

    return {
        "message": f"Sinhronizirano {len(new_emails)} novih emailov",
        "synced": len(new_emails),
        "new_emails": new_emails,
    }
