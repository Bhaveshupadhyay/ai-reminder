import re
from typing import Optional, Tuple
from app.core.config import settings
from app.core.logging import logger


class NotificationFilterService:
    """Fast heuristic filter to ignore non-actionable, system, or spam notifications before LLM invocation."""

    IGNORED_PACKAGES = set(p.lower() for p in settings.IGNORED_NOTIFICATION_PACKAGES)

    # Patterns for system alerts, verification codes, media controls, etc.
    FILTER_PATTERNS = [
        # OTP / 2FA / Login codes
        (
            re.compile(
                r"\b(otp|verification code|security code|use code|is your login code|password reset code|2fa)\b",
                re.I,
            ),
            "Automated OTP / 2FA verification message",
        ),
        # System & Battery warnings
        (
            re.compile(
                r"\b(battery (is )?low|storage full|system update available|downloading\.\.\.|download complete|connected to wi-fi)\b",
                re.I,
            ),
            "System status notification",
        ),
        # Promotional / broadcast spam
        (
            re.compile(
                r"\b(flat \d+% off|\b\d+% discount\b|flash sale|limited period offer|hurry sale ends)\b",
                re.I,
            ),
            "Promotional broadcast offer",
        ),
        # Music / Media playback notifications
        (
            re.compile(r"\b(playing|paused|track playing|buffering)\b", re.I),
            "Media player notification",
        ),
    ]

    @classmethod
    def should_ignore(
        cls,
        source_package: str,
        source_app: str,
        body: str,
        title: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Returns (True, reason) if notification should be ignored without calling AI.
        """
        # 1. Check ignored package list
        pkg = (source_package or "").strip().lower()
        if pkg in cls.IGNORED_PACKAGES:
            return True, f"Package '{source_package}' is in ignored package list"

        # 2. Check for empty or negligible body
        clean_body = (body or "").strip()
        if not clean_body:
            return True, "Notification body is empty"

        # 3. Check regex heuristic patterns
        full_text = f"{title or ''} {clean_body}".strip()
        for pattern, reason in cls.FILTER_PATTERNS:
            if pattern.search(full_text):
                return True, reason

        return False, None
