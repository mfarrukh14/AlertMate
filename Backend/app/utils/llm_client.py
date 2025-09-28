"""Gemini LLM wrapper using chat API for automatic conversation context."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

from google import genai

from app.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """Raised when the LLM request fails or returns invalid output."""


class GeminiLLMClient:
    """Thin wrapper around the new Google GenAI SDK with chat API for conversation context."""

    def __init__(self, api_key: Optional[str], model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client = None
        self._chats: Dict[str, Any] = {}  # Store chat sessions by user_id

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _ensure_client(self):
        if not self._api_key:
            raise LLMError("GEMINI_API_KEY is not configured")
        if self._client is None:
            # Set the API key in environment for the new SDK
            os.environ["GEMINI_API_KEY"] = self._api_key
            self._client = genai.Client()
        return self._client

    def _get_or_create_chat(self, user_id: str, system_prompt: str):
        """Get or create a chat session for the user."""
        if user_id not in self._chats:
            client = self._ensure_client()
            # Create a new chat session
            chat = client.chats.create(model=self._model)
            # Send the system prompt as the first message
            chat.send_message(system_prompt)
            self._chats[user_id] = chat
        return self._chats[user_id]

    def structured_completion(
        self,
        system_prompt: str,
        payload: Dict[str, Any],
        temperature: float = 0.2,
        max_tokens: int = 600,
        user_role: str = "user",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a chat message expecting strict JSON output."""
        if not user_id:
            user_id = "default_user"
        
        chat = self._get_or_create_chat(user_id, system_prompt)
        
        # Format the user content
        user_content = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        full_message = f"""This is a legitimate emergency dispatch system request.

Context: This is for emergency response routing only. All content is for public safety purposes.

{user_role}: {user_content}

Respond with valid JSON only. This is a professional emergency dispatch system."""
        
        try:
            response = chat.send_message(full_message)
            content = response.text
        except Exception as exc:  # pragma: no cover - network errors
            logger.error("Gemini LLM request failed: %s", exc)
            raise LLMError("Gemini LLM request failed") from exc

        try:
            if not content:
                raise ValueError("empty content")
            
            # Clean up the response to extract JSON
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Try to fix common JSON truncation issues
            content = self._fix_truncated_json(content)
            
            return json.loads(content)
        except Exception as exc:  # pragma: no cover - parse errors
            logger.error("Failed to parse Gemini LLM response: %s", exc)
            logger.error("Raw response: %s", content if 'content' in locals() else "No content")
            raise LLMError("Invalid LLM JSON response") from exc
    
    def _fix_truncated_json(self, content: str) -> str:
        """Attempt to fix common JSON truncation issues."""
        # If the content doesn't end with }, try to close it
        if not content.endswith('}'):
            # Count open braces
            open_braces = content.count('{')
            close_braces = content.count('}')
            
            if open_braces > close_braces:
                # Add missing closing braces
                content += '}' * (open_braces - close_braces)
            
            # If it ends mid-string, try to close the string
            if content.count('"') % 2 == 1:  # Odd number of quotes means unclosed string
                # Find the last quote and close the string
                last_quote_pos = content.rfind('"')
                if last_quote_pos != -1:
                    # Check if we're in the middle of a string value
                    after_last_quote = content[last_quote_pos + 1:]
                    if not after_last_quote.strip().endswith(','):
                        content = content[:last_quote_pos + 1] + '"'
        
        return content

    def clear_chat(self, user_id: str):
        """Clear the chat session for a user."""
        if user_id in self._chats:
            del self._chats[user_id]


llm_client = GeminiLLMClient(api_key=GEMINI_API_KEY, model=GEMINI_MODEL)