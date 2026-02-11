"""
Email Send Service - pošiljanje emailov preko MS Graph.

Podpira:
- Nov email
- Reply na obstoječ email (reply_to_message_id)

Zahteva Mail.Send dovoljenje v Azure AD app registration.
"""

import httpx
from typing import Optional

from app.config import get_settings
from app.services.email_sync import get_ms_graph_token

settings = get_settings()


async def send_email_via_graph(
    to: str,
    subject: str,
    body: str,
    reply_to_message_id: Optional[str] = None,
) -> dict:
    """Pošlji email preko MS Graph API.

    Args:
        to: Naslovnik (email naslov)
        subject: Zadeva
        body: Vsebina (HTML ali plain text)
        reply_to_message_id: Outlook message ID za reply

    Returns:
        dict z uspehom ali napako
    """
    token = await get_ms_graph_token()
    if not token:
        return {"success": False, "error": "MS Graph ni na voljo - potrebna konfiguracija"}

    mailbox = settings.ms_graph_mailbox
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    if reply_to_message_id:
        # Reply na obstoječ email
        url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/messages/{reply_to_message_id}/reply"
        payload = {
            "message": {
                "toRecipients": [
                    {"emailAddress": {"address": to}}
                ],
            },
            "comment": body,
        }
    else:
        # Nov email
        url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/sendMail"
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body,
                },
                "toRecipients": [
                    {"emailAddress": {"address": to}}
                ],
            },
            "saveToSentItems": True,
        }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)

            if response.status_code in (200, 202):
                return {
                    "success": True,
                    "message": f"Email poslan na {to}",
                    "subject": subject,
                }
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", {}).get("message", response.text[:200])
                return {
                    "success": False,
                    "error": f"MS Graph napaka ({response.status_code}): {error_msg}",
                }

    except Exception as e:
        return {"success": False, "error": f"Napaka pri pošiljanju: {str(e)}"}
