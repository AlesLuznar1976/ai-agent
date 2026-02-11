from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import check_connection
from app.api import auth, chat, projekti, emaili, dokumenti
from app.api.websocket import router as ws_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print(f"Starting {settings.app_name}...")
    print(f"Environment: {settings.app_env}")

    # Preveri DB povezavo
    if check_connection():
        print("Database connection: OK")
    else:
        print("WARNING: Database connection FAILED!")

    # Zaženi email sync scheduler
    from app.services.scheduler import get_scheduler
    scheduler = get_scheduler()
    await scheduler.start()

    yield

    # Shutdown
    await scheduler.stop()
    print("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="AI Agent sistem za Luznar Electronics",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Avtentikacija"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(projekti.router, prefix="/api/projekti", tags=["Projekti"])
app.include_router(emaili.router, prefix="/api/emaili", tags=["Emaili"])
app.include_router(dokumenti.router, prefix="/api/dokumenti", tags=["Dokumenti"])
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_ok = check_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "app": settings.app_name,
        "env": settings.app_env,
        "database": "connected" if db_ok else "disconnected",
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Dobrodošli v {settings.app_name}",
        "docs": "/docs",
        "health": "/health"
    }
