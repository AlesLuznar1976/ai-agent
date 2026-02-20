"""
Agent Processor - avtomatsko ustvarjanje projektov iz agent mailboxa.

Ko zaposleni posreduje email na agent@luznar.com, ta modul po končani
analizi avtomatsko ustvari projekt in poveže email z njim.
"""

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.crud import emaili as crud_emaili
from app.crud import projekti as crud_projekti


async def process_agent_emails(db: Session) -> int:
    """Obdela analizirane agent emaile in ustvari projekte.

    Za vsak analiziran email na agent@luznar.com brez projekta:
    1. Prebere analiza_rezultat za podatke stranke
    2. Ustvari projekt z imenom stranke in zadevo
    3. Poveže email s projektom
    4. Doda časovnico

    Returns:
        Število ustvarjenih projektov
    """
    ready_emails = crud_emaili.list_agent_emails_ready(db)
    if not ready_emails:
        return 0

    created = 0
    for db_email in ready_emails:
        try:
            _process_single_email(db, db_email)
            created += 1
        except Exception as e:
            print(f"Agent processor error for email {db_email.id}: {e}")

    return created


def _process_single_email(db: Session, db_email) -> None:
    """Obdela en agent email - ustvari projekt in poveže."""

    # Preberi analiza_rezultat
    analiza = _parse_json_field(db_email.analiza_rezultat)
    izvleceni = _parse_json_field(db_email.izvleceni_podatki)

    # Izvleci podatke stranke iz analize
    stranka_ime = None
    povzetek = None
    if analiza:
        stranka = analiza.get("stranka") or {}
        stranka_ime = stranka.get("ime")
        povzetek = analiza.get("povzetek")

    # Fallback na izvlečene podatke iz kategorizacije
    if not stranka_ime and izvleceni:
        stranka_ime = izvleceni.get("stranka_ime") or izvleceni.get("povzetek")

    # Sestavi naziv projekta
    zadeva = db_email.zadeva or "Brez zadeve"
    if stranka_ime:
        naziv = f"{stranka_ime} - {zadeva}"
    else:
        naziv = zadeva
    naziv = naziv[:255]

    # Opombe: povzetek iz analize ali prvih 500 znakov telesa
    if not povzetek:
        povzetek = (db_email.telo or "")[:500]

    # Ustvari projekt
    projekt = crud_projekti.create_projekt(
        db,
        naziv=naziv,
        opombe=povzetek,
        username="agent",
    )

    # Poveži email s projektom
    crud_emaili.update_email(
        db, db_email.id,
        projekt_id=projekt.id,
        status="Dodeljen",
    )

    # Doda časovnico
    crud_projekti.add_casovnica_event(
        db,
        projekt_id=projekt.id,
        dogodek="Email posredovan agentu",
        opis=f"Email '{zadeva}' od {db_email.posiljatelj} avtomatsko dodeljen projektu",
        uporabnik_ali_agent="agent",
    )

    # WebSocket obvestilo
    _notify_new_project(projekt, db_email)

    print(f"Agent processor: created project {projekt.stevilka_projekta} '{naziv}' from email {db_email.id}")


def _parse_json_field(value) -> dict | None:
    """Parsira JSON string polje iz DB."""
    if not value:
        return None
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _notify_new_project(projekt, db_email) -> None:
    """Pošlji WebSocket obvestilo o novem projektu (fire-and-forget)."""
    try:
        import asyncio
        from app.api.websocket import manager

        asyncio.ensure_future(manager.broadcast({
            "type": "new_project",
            "title": "Nov projekt (agent)",
            "message": f"{projekt.stevilka_projekta}: {projekt.naziv}",
            "projekt_id": projekt.id,
            "email_id": db_email.id,
            "timestamp": datetime.now().isoformat(),
        }))
    except Exception as e:
        print(f"Agent processor WebSocket notification error: {e}")
