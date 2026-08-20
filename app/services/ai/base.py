from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from app.schemas.ai import OpenLoopAnalysis


class AIProvider(ABC):
    """Abstract base interface for AI notification analyzers."""

    @abstractmethod
    async def analyze_notification(
        self,
        body: str,
        title: Optional[str] = None,
        sender: Optional[str] = None,
        source_app: Optional[str] = None,
        reference_time: Optional[datetime] = None,
        user_timezone: str = "UTC",
    ) -> OpenLoopAnalysis:
        pass
