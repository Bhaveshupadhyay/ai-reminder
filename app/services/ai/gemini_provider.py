import json
from datetime import datetime, timezone
from typing import Optional
import httpx
from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.core.logging import logger
from app.schemas.ai import OpenLoopAnalysis
from app.services.ai.base import AIProvider
from app.services.date_service import DateService


class GeminiProvider(AIProvider):
    """Google Gemini API provider for open-loop extraction."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.AI_API_KEY
        self.model = model or settings.AI_MODEL or "gemini-3.1-flash-lite"
        if not self.api_key:
            logger.warning("GeminiProvider initialized without AI_API_KEY.")

    async def analyze_notification(
        self,
        body: str,
        title: Optional[str] = None,
        sender: Optional[str] = None,
        source_app: Optional[str] = None,
        reference_time: Optional[datetime] = None,
        user_timezone: str = "UTC",
    ) -> OpenLoopAnalysis:
        if not self.api_key:
            raise AIServiceError("AI_API_KEY is not configured for Gemini provider")

        now_utc = reference_time or datetime.now(timezone.utc)
        prompt = f"""Analyze this notification and extract open-loop task information.
Reference Time (UTC): {now_utc.isoformat()}
User Timezone: {user_timezone}
Source App: {source_app or 'Unknown'}
Sender: {sender or 'Unknown'}
Title: {title or ''}
Body: {body}

Respond with JSON only matching this schema:
{{
  "actionable": boolean,
  "task": string or null,
  "person": string or null,
  "deadline": string (ISO-8601 UTC) or null,
  "deadline_text": string or null,
  "importance": "low" | "medium" | "high" | null,
  "confidence": float,
  "reason": string
}}
"""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }

        try:
            async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise AIServiceError(f"Gemini API returned status {response.status_code}: {response.text}")

                data = response.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(raw_text)

                if parsed.get("deadline_text") and not parsed.get("deadline"):
                    parsed["deadline"] = DateService.parse_relative_deadline(
                        parsed["deadline_text"], reference_time, user_timezone
                    )

                return OpenLoopAnalysis.model_validate(parsed)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            raise AIServiceError(f"Failed to analyze notification with Gemini: {str(e)}")
