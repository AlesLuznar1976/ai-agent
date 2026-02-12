"""
System Status API - celovit monitoring sistema.

Endpointi:
- GET /status  - JSON z metriki (CPU, RAM, GPU, servisi, agent)
- GET /dashboard - HTML dashboard z live grafi
"""

import asyncio
import platform
import time
from datetime import datetime
from pathlib import Path

import httpx
import psutil
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.config import get_settings

router = APIRouter()
settings = get_settings()

_START_TIME = time.time()


# ---------------------------------------------------------------------------
# Helper: system metrics (psutil)
# ---------------------------------------------------------------------------
async def _get_system_metrics() -> dict:
    """CPU, RAM, disk, network prek psutil."""
    # cpu_percent blokira (interval), zato to_thread
    cpu_percent = await asyncio.to_thread(psutil.cpu_percent, interval=1)
    per_cpu = await asyncio.to_thread(psutil.cpu_percent, interval=0, percpu=True)

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    freq = psutil.cpu_freq()

    return {
        "hostname": platform.node(),
        "platform": f"{platform.system()} {platform.release()}",
        "cpu": {
            "percent": cpu_percent,
            "count": psutil.cpu_count(logical=True),
            "freq_mhz": round(freq.current, 0) if freq else None,
            "per_cpu_percent": per_cpu,
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 1),
            "used_gb": round(mem.used / (1024**3), 1),
            "percent": mem.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 1),
            "used_gb": round(disk.used / (1024**3), 1),
            "percent": disk.percent,
        },
        "network": {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "connections_count": len(psutil.net_connections(kind="inet")),
        },
    }


# ---------------------------------------------------------------------------
# Helper: GPU metrics (nvidia-smi)
# ---------------------------------------------------------------------------
async def _get_gpu_metrics() -> dict:
    """GPU info prek nvidia-smi subprocess."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "nvidia-smi",
            "--query-gpu=name,driver_version,temperature.gpu,fan.speed,"
            "power.draw,power.limit,memory.total,memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)

        if proc.returncode != 0:
            return {"available": False}

        line = stdout.decode().strip().split("\n")[0]
        parts = [p.strip() for p in line.split(",")]

        mem_total = float(parts[6])
        mem_used = float(parts[7])
        mem_pct = round(mem_used / mem_total * 100, 1) if mem_total > 0 else 0

        # GPU processes
        proc2 = await asyncio.create_subprocess_exec(
            "nvidia-smi",
            "--query-compute-apps=pid,process_name,used_gpu_memory",
            "--format=csv,noheader,nounits",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout2, _ = await asyncio.wait_for(proc2.communicate(), timeout=5)
        processes = []
        if proc2.returncode == 0:
            for pline in stdout2.decode().strip().split("\n"):
                pline = pline.strip()
                if not pline:
                    continue
                pp = [x.strip() for x in pline.split(",")]
                if len(pp) >= 3:
                    processes.append({
                        "pid": int(pp[0]),
                        "name": pp[1],
                        "memory_mb": float(pp[2]),
                    })

        def _safe_float(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        return {
            "available": True,
            "name": parts[0],
            "driver_version": parts[1],
            "temperature_c": _safe_float(parts[2]),
            "fan_percent": _safe_float(parts[3]),
            "power_draw_w": _safe_float(parts[4]),
            "power_limit_w": _safe_float(parts[5]),
            "memory_total_mb": mem_total,
            "memory_used_mb": mem_used,
            "memory_percent": mem_pct,
            "gpu_utilization_percent": _safe_float(parts[8]),
            "processes": processes,
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Helper: Ollama status
# ---------------------------------------------------------------------------
async def _get_ollama_status() -> dict:
    """Ollama /api/tags + /api/ps."""
    result = {"status": "offline", "response_time_ms": None, "models_available": [], "models_loaded": []}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            t0 = time.time()
            resp = await client.get(f"{settings.ollama_url}/api/tags")
            elapsed = round((time.time() - t0) * 1000, 1)
            result["response_time_ms"] = elapsed

            if resp.status_code == 200:
                result["status"] = "online"
                models = resp.json().get("models", [])
                result["models_available"] = [
                    {
                        "name": m.get("name", ""),
                        "size_gb": round(m.get("size", 0) / (1024**3), 1),
                        "parameter_size": m.get("details", {}).get("parameter_size", ""),
                        "quantization": m.get("details", {}).get("quantization_level", ""),
                    }
                    for m in models
                ]

            # Loaded models (in VRAM)
            resp2 = await client.get(f"{settings.ollama_url}/api/ps")
            if resp2.status_code == 200:
                loaded = resp2.json().get("models", [])
                result["models_loaded"] = [
                    {
                        "name": m.get("name", ""),
                        "size_gb": round(m.get("size", 0) / (1024**3), 1),
                        "vram_gb": round(m.get("size_vram", 0) / (1024**3), 1),
                        "expires_at": m.get("expires_at", ""),
                    }
                    for m in loaded
                ]
    except Exception:
        pass
    return result


# ---------------------------------------------------------------------------
# Helper: Database status
# ---------------------------------------------------------------------------
async def _get_database_status() -> dict:
    """DB health + pool stats."""
    from app.database import engine

    result = {"status": "offline", "response_time_ms": None, "pool_size": None, "pool_checked_out": None}
    try:
        from sqlalchemy import text

        def _check():
            t0 = time.time()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return round((time.time() - t0) * 1000, 1)

        elapsed = await asyncio.to_thread(_check)
        result["status"] = "online"
        result["response_time_ms"] = elapsed

        pool = engine.pool
        result["pool_size"] = pool.size()
        result["pool_checked_out"] = pool.checkedout()
    except Exception as e:
        result["error"] = str(e)
    return result


# ---------------------------------------------------------------------------
# Helper: MS Graph status
# ---------------------------------------------------------------------------
async def _get_ms_graph_status() -> dict:
    """MS Graph token validacija."""
    result = {"status": "not_configured", "token_valid": False, "mailboxes": []}

    if not all([settings.ms_graph_client_id, settings.ms_graph_client_secret, settings.ms_graph_tenant_id]):
        return result

    try:
        from app.services.email_sync import get_ms_graph_token
        token = await get_ms_graph_token()
        result["token_valid"] = token is not None
        result["status"] = "online" if token else "auth_failed"
        result["mailboxes"] = settings.ms_graph_mailboxes
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    return result


# ---------------------------------------------------------------------------
# Helper: Scheduler status
# ---------------------------------------------------------------------------
def _get_scheduler_status() -> dict:
    """Email sync scheduler status."""
    try:
        from app.services.scheduler import get_scheduler
        sched = get_scheduler()
        return {
            "status": "running" if sched._running else ("disabled" if not sched.enabled else "stopped"),
            "enabled": sched.enabled,
            "interval_minutes": sched.interval_minutes,
        }
    except Exception:
        return {"status": "unknown"}


# ---------------------------------------------------------------------------
# Helper: Agent status
# ---------------------------------------------------------------------------
def _get_agent_status() -> dict:
    """Orchestrator info."""
    try:
        from app.agents.orchestrator import get_orchestrator
        orch = get_orchestrator()
        return {
            "orchestrator_model": orch.model,
            "max_tool_rounds": orch.MAX_TOOL_ROUNDS,
            "tool_model": settings.ollama_tool_model,
        }
    except Exception:
        return {"orchestrator_model": "unknown"}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/status")
async def system_status():
    """Celovit status sistema - CPU, RAM, GPU, servisi, agent."""

    # Zaženi vse helper-je vzporedno
    sys_task = _get_system_metrics()
    gpu_task = _get_gpu_metrics()
    ollama_task = _get_ollama_status()
    db_task = _get_database_status()
    graph_task = _get_ms_graph_status()

    system, gpu, ollama, db, ms_graph = await asyncio.gather(
        sys_task, gpu_task, ollama_task, db_task, graph_task
    )

    scheduler = _get_scheduler_status()
    agent = _get_agent_status()

    return {
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(time.time() - _START_TIME),
        "system": system,
        "gpu": gpu,
        "services": {
            "ollama": ollama,
            "database": db,
            "ms_graph": ms_graph,
            "email_scheduler": scheduler,
            "anthropic": {
                "configured": bool(settings.anthropic_api_key),
                "model": settings.anthropic_model,
            },
        },
        "agent": agent,
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """HTML dashboard z live grafi."""
    template_path = Path(__file__).parent.parent / "templates" / "dashboard.html"
    return HTMLResponse(content=template_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Dnevnik napak (log viewer)
# ---------------------------------------------------------------------------
@router.get("/dnevnik")
async def get_logs(
    nivo: str = "WARNING",
    limit: int = 100,
    iskanje: str = "",
):
    """Vrni zadnje log vnose (JSON)."""
    from app.services.log_collector import get_log_collector
    collector = get_log_collector()
    logs = collector.get_logs(level=nivo, limit=limit, search=iskanje or None)
    counts = collector.get_counts()
    return {
        "vnosi": logs,
        "stevci": counts,
        "skupaj": len(logs),
    }


@router.get("/dnevnik-ui", response_class=HTMLResponse)
async def dnevnik_ui():
    """HTML stran za spremljanje napak v slovenščini."""
    template_path = Path(__file__).parent.parent / "templates" / "dnevnik.html"
    return HTMLResponse(content=template_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Email pregled - direktni endpointi (brez LLM)
# ---------------------------------------------------------------------------
@router.get("/email-povzetek")
async def email_povzetek(dni: int = 7, status: str = "Nov"):
    """Direktni povzetek emailov brez LLM."""
    from app.agents.tool_executor import get_tool_executor
    executor = get_tool_executor()
    return executor._summarize_emails({"days": dni, "status": status})


@router.get("/email-dnevno-porocilo")
async def email_dnevno_porocilo(nabiralnik: str = ""):
    """Direktno dnevno poročilo po nabiralnikih brez LLM."""
    from app.agents.tool_executor import get_tool_executor
    executor = get_tool_executor()
    return executor._daily_report({"nabiralnik": nabiralnik})


@router.get("/email-pregled", response_class=HTMLResponse)
async def email_pregled_ui():
    """HTML pregled emailov - direktni prikaz brez LLM."""
    template_path = Path(__file__).parent.parent / "templates" / "email_pregled.html"
    return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
