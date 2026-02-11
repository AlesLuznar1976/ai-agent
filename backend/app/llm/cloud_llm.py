from typing import Optional
from openai import AsyncOpenAI

from app.config import get_settings

settings = get_settings()


class CloudLLM:
    """Povezava z OpenAI (cloud LLM)"""

    def __init__(self):
        self.model = settings.openai_model
        self.client: Optional[AsyncOpenAI] = None

        if settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Pošlje prompt na OpenAI in vrne odgovor.

        Args:
            prompt: Uporabniški prompt
            system_prompt: Sistemski prompt (opcijsko)
        """

        if not self.client:
            raise Exception("OpenAI API ključ ni konfiguriran")

        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
        )

        return response.choices[0].message.content or ""

    async def complete_with_json(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Vrne odgovor v JSON formatu"""

        if not self.client:
            raise Exception("OpenAI API ključ ni konfiguriran")

        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

        return response.choices[0].message.content or "{}"

    async def is_available(self) -> bool:
        """Preveri ali je OpenAI API dosegljiv"""
        if not self.client:
            return False

        try:
            # Preprost test
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False
