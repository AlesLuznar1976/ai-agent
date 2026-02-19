"""Batch RFQ analysis - poženi z: python3 run_batch_analysis.py"""
import asyncio
import time
import sys

sys.path.insert(0, "/app")

from app.database import SessionLocal
from app.services.rfq_analyzer import analyze_rfq_email
from app.crud import emaili as crud_emaili


async def run_all():
    db = SessionLocal()
    try:
        pending = crud_emaili.list_emails_pending_analysis(db)
        total = len(pending)
        print(f"Začenjam analizo {total} emailov...", flush=True)

        success = 0
        errors = 0
        start = time.time()

        for i, email in enumerate(pending):
            try:
                await analyze_rfq_email(db, email.id)
                success += 1
                elapsed = time.time() - start
                avg = elapsed / (i + 1)
                remaining = avg * (total - i - 1)
                print(f"[{i+1}/{total}] Email {email.id} OK ({elapsed:.0f}s, ~{remaining/60:.0f}min preostalo)", flush=True)
            except Exception as e:
                errors += 1
                print(f"[{i+1}/{total}] Email {email.id} NAPAKA: {str(e)[:100]}", flush=True)

        elapsed = time.time() - start
        print(f"\nKONČANO: {success} uspešnih, {errors} napak, {elapsed/60:.1f} minut", flush=True)
    finally:
        db.close()


asyncio.run(run_all())
