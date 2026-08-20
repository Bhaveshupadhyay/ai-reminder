import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Set, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import EntityNotFoundError
from app.core.logging import logger
from app.models.open_loop import OpenLoop
from app.repositories.open_loop_repository import OpenLoopRepository
from app.schemas.ai import OpenLoopAnalysis
from app.schemas.open_loop import OpenLoopUpdate

STOPWORDS: Set[str] = {
    "the", "a", "an", "on", "to", "for", "me", "you", "and", "or", "in",
    "at", "by", "of", "with", "just", "checking", "follow", "up", "can",
    "please", "hey", "hi", "if", "got", "chance", "look", "is", "that",
    "about", "this", "my", "your"
}

IMPORTANCE_RANKS = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


def extract_keywords(text: str) -> Set[str]:
    """Extract normalized meaningful tokens excluding common stopwords."""
    words = re.findall(r"\w+", (text or "").lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 1}


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between token sets of two text snippets."""
    set1 = extract_keywords(text1)
    set2 = extract_keywords(text2)
    if not set1 or not set2:
        return 0.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)


class OpenLoopService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OpenLoopRepository(db)

    async def get_by_id(self, open_loop_id: uuid.UUID) -> OpenLoop:
        open_loop = await self.repo.get_by_id(open_loop_id)
        if not open_loop:
            raise EntityNotFoundError("OpenLoop", open_loop_id)
        return open_loop

    async def find_matching_open_loop(
        self,
        user_id: uuid.UUID,
        analysis: OpenLoopAnalysis,
    ) -> Optional[OpenLoop]:
        """
        Deduplication matching:
        Attempts to associate a new actionable message with an existing open loop
        based on user_id, person match, task similarity, and recency.
        """
        if not analysis.task:
            return None

        recent_open_loops = await self.repo.find_recent_open_by_user(
            user_id=user_id, window_days=settings.DEDUPLICATION_WINDOW_DAYS
        )
        if not recent_open_loops:
            return None

        candidate_person = (analysis.person or "").strip().lower()
        new_keywords = extract_keywords(analysis.task)

        best_match: Optional[OpenLoop] = None
        best_score = 0.0

        for existing in recent_open_loops:
            score = 0.0
            existing_person = (existing.person or "").strip().lower()

            # Person match score
            person_matched = False
            if candidate_person and existing_person:
                if candidate_person == existing_person or candidate_person in existing_person or existing_person in candidate_person:
                    person_matched = True
                    score += 0.25
            elif not candidate_person and not existing_person:
                score += 0.1

            # Task similarity score
            sim = calculate_similarity(analysis.task, existing.task)
            score += sim * 0.65

            # Key concept overlap (e.g. "deck", "proposal", "contract", "invoice")
            existing_keywords = extract_keywords(existing.task)
            common_keywords = new_keywords.intersection(existing_keywords)
            if common_keywords:
                score += 0.30

            if score > best_score:
                best_score = score
                best_match = existing

        threshold = settings.DEDUPLICATION_SIMILARITY_THRESHOLD
        if best_match and best_score >= threshold:
            logger.info(
                f"Deduplication matched existing OpenLoop {best_match.id} with score {best_score:.2f}"
            )
            return best_match

        return None

    async def process_actionable_notification(
        self,
        user_id: uuid.UUID,
        notification_id: uuid.UUID,
        analysis: OpenLoopAnalysis,
    ) -> Tuple[OpenLoop, bool]:
        """
        Processes an actionable analysis:
        Updates existing open loop if matching, otherwise creates a new open loop.
        Returns (open_loop, is_new_created).
        """
        existing_match = await self.find_matching_open_loop(user_id, analysis)

        if existing_match:
            # Update existing open loop
            updates:dict[str,Any] = {
                "updated_at": datetime.now(timezone.utc),
                "source_notification_id": notification_id,
            }
            if analysis.deadline:
                updates["deadline"] = analysis.deadline
                updates["deadline_text"] = analysis.deadline_text

            # Update importance if new one is higher
            if analysis.importance:
                curr_rank = IMPORTANCE_RANKS.get(existing_match.importance or "medium", 2)
                new_rank = IMPORTANCE_RANKS.get(analysis.importance, 2)
                if new_rank > curr_rank:
                    updates["importance"] = analysis.importance

            if analysis.reason:
                updates["reason"] = f"{existing_match.reason} | Follow-up: {analysis.reason}"

            updated = await self.repo.update(existing_match, updates)
            return updated, False

        # Create new open loop
        new_open_loop = OpenLoop(
            user_id=user_id,
            source_notification_id=notification_id,
            task=analysis.task or "Action required",
            person=analysis.person,
            deadline=analysis.deadline,
            deadline_text=analysis.deadline_text,
            importance=analysis.importance or "medium",
            confidence=analysis.confidence,
            reason=analysis.reason,
            status="open",
        )
        created = await self.repo.create(new_open_loop)
        return created, True

    async def update_open_loop(
        self, open_loop_id: uuid.UUID, data: OpenLoopUpdate
    ) -> OpenLoop:
        open_loop = await self.get_by_id(open_loop_id)
        update_dict = data.model_dump(exclude_unset=True)
        if data.status == "completed" and open_loop.status != "completed":
            update_dict["completed_at"] = datetime.now(timezone.utc)
        elif data.status and data.status != "completed":
            update_dict["completed_at"] = None

        update_dict["updated_at"] = datetime.now(timezone.utc)
        return await self.repo.update(open_loop, update_dict)

    async def complete_open_loop(self, open_loop_id: uuid.UUID) -> OpenLoop:
        open_loop = await self.get_by_id(open_loop_id)
        now = datetime.now(timezone.utc)
        return await self.repo.update(
            open_loop,
            {"status": "completed", "completed_at": now, "updated_at": now},
        )

    async def dismiss_open_loop(self, open_loop_id: uuid.UUID) -> OpenLoop:
        open_loop = await self.get_by_id(open_loop_id)
        return await self.repo.update(
            open_loop,
            {"status": "dismissed", "updated_at": datetime.now(timezone.utc)},
        )

    async def list_open_loops(
        self,
        user_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[OpenLoop], int]:
        return await self.repo.list_open_loops(
            user_id=user_id, status=status, limit=limit, offset=offset
        )
