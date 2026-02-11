"""
Email Sync Service - sinhronizacija emailov iz MS Graph.

Centralna logika ki jo kličeta API endpoint in tool executor.
"""

import httpx
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.config import get_settings
from app.crud import emaili as crud_emaili
from app.agents.email_agent import get_email_agent
from app.utils.html_utils import strip_html_to_text

settings = get_settings()


async def get_ms_graph_token() -> Optional[str]:
    """Pridobi MS Graph access token."""
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


async def fetch_emails_from_graph(
    token: str,
    top: int = 50,
    since: Optional[datetime] = None,
) -> list[dict]:
    """Pridobi emaile iz MS Graph s paginacijo.

    Args:
        token: MS Graph access token
        top: Število emailov na stran
        since: Filtrira emaile od tega datuma naprej
    """
    mailbox = settings.ms_graph_mailbox
    url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/messages"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "$top": min(top, 50),
        "$orderby": "receivedDateTime desc",
        "$select": "id,subject,from,toRecipients,body,receivedDateTime,hasAttachments",
    }

    if since:
        params["$filter"] = f"receivedDateTime ge {since.strftime('%Y-%m-%dT%H:%M:%SZ')}"

    all_emails = []
    consecutive_existing = 0
    max_consecutive = 3

    async with httpx.AsyncClient(timeout=30.0) as client:
        while url:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code != 200:
                break

            data = response.json()
            emails = data.get("value", [])
            all_emails.extend(emails)

            # Podpora za @odata.nextLink paginacijo
            next_link = data.get("@odata.nextLink")
            if next_link and len(all_emails) < top:
                url = next_link
                params = {}  # nextLink že vsebuje parametre
            else:
                break

    return all_emails


async def sync_emails_from_outlook(
    db: Session,
    top: int = 50,
) -> dict:
    """Sinhroniziraj emaile iz Outlook.

    Centralna funkcija ki jo kličeta API endpoint in tool executor.

    Returns:
        dict z message, synced count, new_emails seznam
    """
    token = await get_ms_graph_token()
    if not token:
        return {
            "message": "Email sinhronizacija ni na voljo - potrebna MS Graph konfiguracija",
            "synced": 0,
            "new_emails": [],
        }

    # Pridobi datum zadnjega emaila za inkrementalno sinhronizacijo
    since = crud_emaili.get_latest_email_date(db)

    graph_emails = await fetch_emails_from_graph(token, top=top, since=since)
    email_agent = get_email_agent()
    new_emails = []
    consecutive_existing = 0

    for msg in graph_emails:
        outlook_id = msg.get("id", "")

        # Preskoči če že obstaja
        existing = crud_emaili.get_email_by_outlook_id(db, outlook_id)
        if existing:
            consecutive_existing += 1
            if consecutive_existing >= 3:
                break
            continue
        consecutive_existing = 0

        zadeva = msg.get("subject", "Brez zadeve")
        from_data = msg.get("from", {}).get("emailAddress", {})
        posiljatelj = f"{from_data.get('name', '')} <{from_data.get('address', '')}>"
        prejemniki_list = msg.get("toRecipients", [])
        prejemniki = ", ".join(
            r.get("emailAddress", {}).get("address", "") for r in prejemniki_list
        )
        raw_body = msg.get("body", {}).get("content", "")
        has_attachments = msg.get("hasAttachments", False)
        datum_str = msg.get("receivedDateTime", "")

        # Počisti HTML
        clean_body = strip_html_to_text(raw_body)

        try:
            datum = datetime.fromisoformat(datum_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            datum = datetime.now()

        # AI kategorizacija z EmailAgent
        attachment_names = []
        if has_attachments:
            att_meta = await _fetch_attachment_names(token, outlook_id)
            attachment_names = [a.get("name", "") for a in att_meta]

        analysis = await email_agent.categorize_email(
            sender=posiljatelj,
            subject=zadeva,
            body=clean_body,
            attachments=attachment_names,
        )

        # Pripravi izvlečene podatke
        izvleceni = {
            "kategorija": analysis.kategorija.value,
            "zaupanje": analysis.zaupanje,
            "povzetek": analysis.povzetek,
            "predlagan_projekt_id": analysis.predlagan_projekt_id,
            **analysis.izvleceni_podatki,
        }

        # Pripravi priloge metadata (brez prenosa)
        priloge_meta = None
        if has_attachments and attachment_names:
            priloge_meta = [{"name": n, "downloaded": False} for n in attachment_names]

        # Shrani v bazo
        db_email = crud_emaili.create_email(
            db,
            outlook_id=outlook_id,
            zadeva=zadeva,
            posiljatelj=posiljatelj,
            prejemniki=prejemniki,
            telo=clean_body[:4000],
            kategorija=analysis.kategorija.value,
            datum=datum,
            izvleceni_podatki=izvleceni,
            priloge=priloge_meta,
        )

        new_emails.append(_db_email_to_dict(db_email))

    return {
        "message": f"Sinhronizirano {len(new_emails)} novih emailov",
        "synced": len(new_emails),
        "new_emails": new_emails,
    }


async def _fetch_attachment_names(token: str, message_id: str) -> list[dict]:
    """Pridobi seznam prilog emaila (samo imena/metadata)."""
    mailbox = settings.ms_graph_mailbox
    url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/messages/{message_id}/attachments"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"$select": "id,name,size,contentType"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json().get("value", [])
    except Exception:
        pass
    return []


def _db_email_to_dict(db_email) -> dict:
    """Pretvori DB email v dict za response."""
    import json

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
