import re
from datetime import datetime
from typing import Optional
from app.schemas.ai import OpenLoopAnalysis
from app.services.ai.base import AIProvider
from app.services.date_service import DateService


class MockAIProvider(AIProvider):
    """Deterministic Mock AI Provider for testing and local development without API keys."""

    async def analyze_notification(
        self,
        body: str,
        title: Optional[str] = None,
        sender: Optional[str] = None,
        source_app: Optional[str] = None,
        reference_time: Optional[datetime] = None,
        user_timezone: str = "UTC",
    ) -> OpenLoopAnalysis:
        text = body.strip()
        lower_text = text.lower()
        effective_person = sender or title

        # Non-actionable deterministic test cases
        non_actionable_patterns = [
            r"^(lol|haha|lmao|rofl|omg|wow|nice|ok|k|cool|sure|great|thanks|thank you)[\s\.\!😂🤣👍❤️]*$",
            r"lol that'?s (crazy|hilarious|funny|wild|insane)",
            r"^sounds good",
            r"^see you (there|soon)",
            r"happy birthday",
            r"congratulations",
        ]
        for pattern in non_actionable_patterns:
            if re.search(pattern, lower_text, re.I):
                return OpenLoopAnalysis(
                    actionable=False,
                    task=None,
                    person=None,
                    deadline=None,
                    deadline_text=None,
                    importance=None,
                    confidence=0.98,
                    reason="This is casual conversation and does not contain an actionable request.",
                )

        # 1. "Can you send me the investor deck tomorrow?"
        if "investor deck" in lower_text or ("send" in lower_text and "deck" in lower_text):
            deadline_text = "tomorrow" if "tomorrow" in lower_text else None
            deadline_dt = DateService.parse_relative_deadline(deadline_text, reference_time, user_timezone)
            return OpenLoopAnalysis(
                actionable=True,
                task="Send the investor deck",
                person=effective_person or "Rahul",
                deadline=deadline_dt,
                deadline_text=deadline_text,
                importance="medium",
                confidence=0.96,
                reason="The sender explicitly requested an action.",
            )

        # 2. "Hey, just checking on that deck" or "checking if you got a chance to look at the proposal"
        if "checking on that deck" in lower_text or "checking on the deck" in lower_text:
            return OpenLoopAnalysis(
                actionable=True,
                task="Send the investor deck",
                person=effective_person or "Rahul",
                deadline=None,
                deadline_text=None,
                importance="high",
                confidence=0.95,
                reason="Follow-up inquiry regarding the investor deck.",
            )

        if "proposal" in lower_text:
            return OpenLoopAnalysis(
                actionable=True,
                task="Review proposal",
                person=effective_person,
                deadline=None,
                deadline_text=None,
                importance="high",
                confidence=0.94,
                reason="The sender is following up on a pending proposal review.",
            )

        # 3. "Let's catch up sometime next week"
        if "catch up" in lower_text or "meet up" in lower_text:
            deadline_text = "next week" if "next week" in lower_text else None
            deadline_dt = DateService.parse_relative_deadline(deadline_text, reference_time, user_timezone)
            return OpenLoopAnalysis(
                actionable=True,
                task="Catch up",
                person=effective_person,
                deadline=deadline_dt,
                deadline_text=deadline_text,
                importance="low",
                confidence=0.90,
                reason="Invitation/follow-up meeting proposed.",
            )

        # 4. "Please call me after 6" / "call me"
        if "call me" in lower_text or "call back" in lower_text or "give me a call" in lower_text:
            deadline_text = None
            if "after 6" in lower_text:
                deadline_text = "after 6"
            elif "tomorrow" in lower_text:
                deadline_text = "tomorrow"
            deadline_dt = DateService.parse_relative_deadline(deadline_text, reference_time, user_timezone)
            return OpenLoopAnalysis(
                actionable=True,
                task=f"Call {effective_person}" if effective_person else "Call sender",
                person=effective_person,
                deadline=deadline_dt,
                deadline_text=deadline_text,
                importance="medium",
                confidence=0.95,
                reason="Direct request to call.",
            )

        # 5. General heuristics for actionable requests
        action_keywords = ["please", "can you", "could you", "need to", "remember to", "don't forget", "review", "send", "submit", "pay", "buy"]
        has_action_cue = any(kw in lower_text for kw in action_keywords)

        deadline_text = None
        for candidate in ["tomorrow", "tonight", "today", "next week", "friday", "monday", "in 2 hours", "after 6"]:
            if candidate in lower_text:
                deadline_text = candidate
                break

        if has_action_cue:
            deadline_dt = DateService.parse_relative_deadline(deadline_text, reference_time, user_timezone)
            clean_task = re.sub(r"^(can you|could you|please|hey|hi|hello)\s+", "", text, flags=re.I).strip()
            clean_task = clean_task.rstrip("?.!")
            if len(clean_task) > 60:
                clean_task = clean_task[:57] + "..."

            return OpenLoopAnalysis(
                actionable=True,
                task=clean_task or "Follow up on request",
                person=effective_person,
                deadline=deadline_dt,
                deadline_text=deadline_text,
                importance="medium",
                confidence=0.88,
                reason="Actionable cue detected in message content.",
            )

        # Default fallback: non-actionable
        return OpenLoopAnalysis(
            actionable=False,
            task=None,
            person=None,
            deadline=None,
            deadline_text=None,
            importance=None,
            confidence=0.85,
            reason="No actionable obligation, question, or task identified.",
        )
