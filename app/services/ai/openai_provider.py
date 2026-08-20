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

SYSTEM_PROMPT = """You are an expert AI assistant that analyzes notifications and detects actionable open loops (tasks, obligations, reminders, follow-ups).
For each notification, return a JSON object with EXACTLY this structure:
{
  "actionable": boolean,
  "task": string or null (short, clear task description),
  "person": string or null (person name involved or requester),
  "deadline": string (ISO-8601 UTC timestamp) or null,
  "deadline_text": string or null (raw phrase mentioned, e.g. 'tomorrow', 'Friday at 5pm'),
  "importance": "low" | "medium" | "high" | null,
  "confidence": float (0.0 to 1.0),
  "reason": string (explanation)
}

Rules:
1. If the message is casual chatter (e.g. "lol that's hilarious", "sounds good"), set actionable=false and other fields to null.
2. If actionable, extract the clear task, person, importance, and reason.
3. If a relative date is mentioned (e.g. 'tomorrow', 'Friday', 'after 6pm'), compute the absolute ISO-8601 UTC timestamp using the provided current reference time and user timezone.
"""


class OpenAIProvider(AIProvider):
    """OpenAI / OpenAI-compatible API provider for open-loop extraction."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.AI_API_KEY
        self.model = model or settings.AI_MODEL or "gpt-4o-mini"
        if not self.api_key:
            logger.warning("OpenAIProvider initialized without AI_API_KEY. Calls will fail unless configured.")

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
            raise AIServiceError("AI_API_KEY is not configured for OpenAI provider")

        now_utc = reference_time or datetime.now(timezone.utc)
        user_prompt = f"""Reference Time (UTC): {now_utc.isoformat()}
User Timezone: {user_timezone}
Source App: {source_app or 'Unknown'}
Sender: {sender or 'Unknown'}
Title: {title or ''}
Body: {body}
"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                if response.status_code != 200:
                    raise AIServiceError(f"OpenAI API returned status {response.status_code}: {response.text}")

                data = response.json()
                raw_content = data["choices"][0]["message"]["content"]
                parsed = json.loads(raw_content)

                if parsed.get("deadline_text") and not parsed.get("deadline"):
                    parsed["deadline"] = DateService.parse_relative_deadline(
                        parsed["deadline_text"], reference_time, user_timezone
                    )

                return OpenLoopAnalysis.model_validate(parsed)
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {str(e)}")
            raise AIServiceError(f"Failed to analyze notification: {str(e)}")
