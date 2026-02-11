import httpx
from typing import Optional

from app.config import get_settings

settings = get_settings()


class LocalLLM:
    """Povezava z Ollama (lokalni LLM)"""

    def __init__(self):
        self.base_url = settings.ollama_url
        self.model = settings.ollama_model
        self.timeout = 120.0  # 2 minuti za dolge odgovore

    async def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Pošlje prompt na Ollama in vrne odgovor.

        Args:
            prompt: Uporabniški prompt
            system_prompt: Sistemski prompt (opcijsko)
        """

        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                }
            )

            if response.status_code != 200:
                raise Exception(f"Ollama napaka: {response.status_code} - {response.text}")

            data = response.json()
            return data.get("message", {}).get("content", "")

    async def generate(self, prompt: str) -> str:
        """Enostavnejši generate API (brez chat formata)"""

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                }
            )

            if response.status_code != 200:
                raise Exception(f"Ollama napaka: {response.status_code}")

            data = response.json()
            return data.get("response", "")

    async def is_available(self) -> bool:
        """Preveri ali je Ollama dosegljiv"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """Vrne seznam razpoložljivih modelov"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []
