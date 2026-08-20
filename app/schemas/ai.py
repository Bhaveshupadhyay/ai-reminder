from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class OpenLoopAnalysis(BaseModel):
    """Strict structured output for AI notification analysis."""

    actionable: bool = Field(
        ...,
        description="Whether this notification contains an actionable open loop, reminder, or follow-up.",
        examples=[True, False],
    )
    task: Optional[str] = Field(
        default=None,
        description="Concise actionable task title or action required.",
        examples=["Send the investor deck"],
    )
    person: Optional[str] = Field(
        default=None,
        description="Name of the requester or person associated with this task.",
        examples=["Rahul"],
    )
    deadline: Optional[datetime] = Field(
        default=None,
        description="Normalized absolute deadline timestamp in UTC.",
        examples=["2026-08-20T17:00:00Z"],
    )
    deadline_text: Optional[str] = Field(
        default=None,
        description="Raw deadline phrase mentioned in the message.",
        examples=["tomorrow"],
    )
    importance: Optional[Literal["low", "medium", "high"]] = Field(
        default=None,
        description="Assessed importance level of the obligation.",
        examples=["medium"],
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the classification from 0.0 to 1.0.",
        examples=[0.96],
    )
    reason: str = Field(
        ...,
        description="Explanation for why this message is or is not actionable.",
        examples=["The sender explicitly requested an action."],
    )
