from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Konfiguracija aplikacije"""

    # Aplikacija
    app_name: str = "AI Agent Sistem"
    app_env: str = "development"
    debug: bool = True

    # Baza podatkov
    database_url: str = "mssql+pyodbc://user:pass@LUZNAR-2018%5CLARGO/LUZNAR?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"

    # JWT
    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # Ollama (lokalni LLM)
    ollama_url: str = "http://192.168.0.66:11434"
    ollama_model: str = "llama3:8b"
    ollama_tool_model: Optional[str] = None  # Model za tool use (npr. llama4:scout)

    # OpenAI (cloud LLM)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo"

    # Anthropic Claude (za pisanje skript)
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-5-20250929"

    # Microsoft Graph
    ms_graph_client_id: Optional[str] = None
    ms_graph_client_secret: Optional[str] = None
    ms_graph_tenant_id: Optional[str] = None
    ms_graph_mailbox: Optional[str] = None  # Lahko več, ločenih z vejico

    @property
    def ms_graph_mailboxes(self) -> list[str]:
        """Vrni seznam vseh mailboxov za sinhronizacijo."""
        if not self.ms_graph_mailbox:
            return []
        return [m.strip() for m in self.ms_graph_mailbox.split(",") if m.strip()]

    # CalcuQuote
    calcuquote_api_key: Optional[str] = None
    calcuquote_url: str = "https://api.calcuquote.com/v1"

    # Email sync
    email_sync_interval_minutes: int = 5
    email_sync_enabled: bool = True

    # Šifriranje
    encryption_key: Optional[str] = None

    # CORS - string ker pydantic-settings ne zna parsati list iz env
    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins_list(self) -> list[str]:
        """Vrni CORS origins kot seznam"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
