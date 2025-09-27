"""Groq LLM wrapper for structured chat completions."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """Raised when the LLM request fails or returns invalid output."""


class GroqLLMClient:
    """Thin wrapper around the Groq chat completions API with JSON output."""

    def __init__(self, api_key: Optional[str], model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client: Optional[Groq] = None

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _ensure_client(self) -> Groq:
        if not self._api_key:
            raise LLMError("GROQ_API_KEY is not configured")
        if self._client is None:
            self._client = Groq(api_key=self._api_key)
        return self._client

    def structured_completion(
        self,
        system_prompt: str,
        payload: Dict[str, Any],
        temperature: float = 0.2,
        max_tokens: int = 600,
        user_role: str = "user",
    ) -> Dict[str, Any]:
        """Send a chat completion request expecting strict JSON output."""
        client = self._ensure_client()
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {
                "role": user_role,
                "content": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            },
        ]
        try:
            response = client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
            )
        except Exception as exc:  # pragma: no cover - network errors
            logger.error("Groq LLM request failed: %s", exc)
            raise LLMError("Groq LLM request failed") from exc

        try:
            content = response.choices[0].message.content
            if not content:
                raise ValueError("empty content")
            return json.loads(content)
        except Exception as exc:  # pragma: no cover - parse errors
            logger.error("Failed to parse Groq LLM response: %s", exc)
            raise LLMError("Invalid LLM JSON response") from exc


llm_client = GroqLLMClient(api_key=GROQ_API_KEY, model=GROQ_MODEL)
