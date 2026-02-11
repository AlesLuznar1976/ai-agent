from typing import Optional
from enum import Enum

from app.config import get_settings

settings = get_settings()


class TaskType(str, Enum):
    """Tipi nalog za LLM"""
    INTENT_RECOGNITION = "intent_recognition"
    EMAIL_CATEGORIZATION = "email_categorization"
    DATA_EXTRACTION = "data_extraction"
    SIMPLE_QUERY = "simple_query"
    DOCUMENT_GENERATION = "document_generation"
    COMPLEX_REASONING = "complex_reasoning"
    EMAIL_COMPOSITION = "email_composition"


class LLMRouter:
    """Usmerja zahteve na pravi LLM (lokalni ali cloud)"""

    # Naloge za lokalni LLM
    LOCAL_TASKS = {
        TaskType.INTENT_RECOGNITION,
        TaskType.EMAIL_CATEGORIZATION,
        TaskType.DATA_EXTRACTION,
        TaskType.SIMPLE_QUERY,
    }

    # Naloge za cloud LLM
    CLOUD_TASKS = {
        TaskType.DOCUMENT_GENERATION,
        TaskType.COMPLEX_REASONING,
        TaskType.EMAIL_COMPOSITION,
    }

    def __init__(self):
        from app.llm.local_llm import LocalLLM
        from app.llm.cloud_llm import CloudLLM

        self.local_llm = LocalLLM()
        self.cloud_llm = CloudLLM()

    async def complete(
        self,
        prompt: str,
        task_type: TaskType = TaskType.SIMPLE_QUERY,
        contains_sensitive: bool = False,
        force_local: bool = False,
        force_cloud: bool = False,
    ) -> str:
        """
        Pošlje prompt na ustrezen LLM.

        Args:
            prompt: Besedilo za LLM
            task_type: Tip naloge
            contains_sensitive: Ali vsebuje občutljive podatke
            force_local: Prisili uporabo lokalnega LLM
            force_cloud: Prisili uporabo cloud LLM
        """

        # Občutljivi podatki vedno lokalno
        if contains_sensitive or force_local:
            return await self._try_local_with_fallback(prompt)

        # Prisili cloud
        if force_cloud:
            return await self._try_cloud_with_fallback(prompt)

        # Routing glede na tip naloge
        if task_type in self.LOCAL_TASKS:
            return await self._try_local_with_fallback(prompt)
        else:
            return await self._try_cloud_with_fallback(prompt)

    async def _try_local_with_fallback(self, prompt: str) -> str:
        """Poskusi lokalni LLM, fallback na cloud"""
        try:
            return await self.local_llm.complete(prompt)
        except Exception as e:
            print(f"Lokalni LLM napaka: {e}, poskušam cloud...")
            return await self.cloud_llm.complete(prompt)

    async def _try_cloud_with_fallback(self, prompt: str) -> str:
        """Poskusi cloud LLM, fallback na lokalni"""
        try:
            return await self.cloud_llm.complete(prompt)
        except Exception as e:
            print(f"Cloud LLM napaka: {e}, poskušam lokalni...")
            return await self.local_llm.complete(prompt)


# Singleton instance
_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Vrne LLM router singleton"""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
