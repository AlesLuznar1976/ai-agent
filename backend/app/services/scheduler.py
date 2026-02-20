"""
Email Sync Scheduler - periodična sinhronizacija emailov.

Asyncio scheduler ki vsakih N minut sinhronizira emaile
iz Outlook in pošlje WebSocket obvestila za nove emaile.
"""

import asyncio
from datetime import datetime

from app.config import get_settings

settings = get_settings()


class EmailSyncScheduler:
    """Periodično sinhronizira emaile iz Outlook."""

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._running = False
        self.interval_minutes = settings.email_sync_interval_minutes
        self.enabled = settings.email_sync_enabled

    async def start(self):
        """Zaženi scheduler."""
        if not self.enabled:
            print("Email sync scheduler: disabled")
            return

        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._sync_loop())
        print(f"Email sync scheduler: started (every {self.interval_minutes} min)")

    async def stop(self):
        """Ustavi scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        print("Email sync scheduler: stopped")

    async def _sync_loop(self):
        """Glavna zanka za periodično sinhronizacijo."""
        # Počakaj 30 sekund po zagonu (počakaj da se app inicializira)
        await asyncio.sleep(30)

        while self._running:
            try:
                await self._do_sync()
            except Exception as e:
                print(f"Email sync scheduler error: {e}")

            # Počakaj do naslednje sinhronizacije
            await asyncio.sleep(self.interval_minutes * 60)

    async def _do_sync(self):
        """Izvedi eno sinhronizacijo."""
        from app.database import SessionLocal
        from app.services.email_sync import sync_emails_from_outlook

        print(f"[{datetime.now().isoformat()}] Email sync: starting...")

        db = SessionLocal()
        try:
            result = await sync_emails_from_outlook(db)
            synced = result.get("synced", 0)

            if synced > 0:
                print(f"Email sync: {synced} new emails")
                # Pošlji WebSocket obvestila
                await self._notify_new_emails(result.get("new_emails", []))
            else:
                print("Email sync: no new emails")

            # Po sync-u obdelaj čakajoče RFQ analize
            try:
                from app.services.rfq_analyzer import process_pending_analyses
                analyzed = await process_pending_analyses(db)
                if analyzed > 0:
                    print(f"RFQ analysis: {analyzed} emails analyzed")
            except Exception as e:
                print(f"RFQ analysis scheduler error: {e}")

            # Po analizi obdelaj agent emaile (ustvari projekte)
            try:
                from app.services.agent_processor import process_agent_emails
                created = await process_agent_emails(db)
                if created > 0:
                    print(f"Agent processor: {created} projects created")
            except Exception as e:
                print(f"Agent processor scheduler error: {e}")

        finally:
            db.close()

    async def _notify_new_emails(self, new_emails: list[dict]):
        """Pošlji WebSocket obvestila za nove emaile."""
        try:
            from app.api.websocket import manager

            for email in new_emails:
                await manager.broadcast({
                    "type": "new_email",
                    "title": "Nov email",
                    "message": f"Od: {email.get('posiljatelj', '?')} - {email.get('zadeva', '?')}",
                    "email_id": email.get("id"),
                    "kategorija": email.get("kategorija"),
                    "timestamp": datetime.now().isoformat(),
                })
        except Exception as e:
            print(f"WebSocket notification error: {e}")


# Singleton
_scheduler: EmailSyncScheduler | None = None


def get_scheduler() -> EmailSyncScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = EmailSyncScheduler()
    return _scheduler
