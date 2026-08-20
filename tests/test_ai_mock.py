from datetime import datetime, timezone
import pytest
from app.services.ai.mock import MockAIProvider


@pytest.mark.asyncio
async def test_mock_investor_deck_actionable():
    provider = MockAIProvider()
    ref = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
    res = await provider.analyze_notification(
        body="Can you send me the investor deck tomorrow?",
        sender="Rahul",
        source_app="WhatsApp",
        reference_time=ref,
        user_timezone="UTC",
    )
    assert res.actionable is True
    assert res.task == "Send the investor deck"
    assert res.person == "Rahul"
    assert res.deadline_text == "tomorrow"
    assert res.deadline is not None
    assert res.confidence >= 0.90


@pytest.mark.asyncio
async def test_mock_casual_non_actionable():
    provider = MockAIProvider()
    for text in ["lol that's crazy 😂", "lol that's hilarious 😂", "sounds good", "thanks!"]:
        res = await provider.analyze_notification(
            body=text,
            sender="Friend",
            source_app="WhatsApp",
        )
        assert res.actionable is False
        assert res.task is None
        assert res.deadline is None


@pytest.mark.asyncio
async def test_mock_catch_up():
    provider = MockAIProvider()
    ref = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
    res = await provider.analyze_notification(
        body="Let's catch up sometime next week.",
        sender="Sarah",
        source_app="Slack",
        reference_time=ref,
    )
    assert res.actionable is True
    assert "Catch up" in res.task
    assert res.person == "Sarah"
    assert res.deadline_text == "next week"


@pytest.mark.asyncio
async def test_mock_call_after_6():
    provider = MockAIProvider()
    ref = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
    res = await provider.analyze_notification(
        body="Please call me after 6.",
        sender="Dr. Smith",
        source_app="SMS",
        reference_time=ref,
    )
    assert res.actionable is True
    assert "Call" in res.task
    assert res.deadline_text == "after 6"
    assert res.deadline is not None


@pytest.mark.asyncio
async def test_mock_proposal_followup():
    provider = MockAIProvider()
    res = await provider.analyze_notification(
        body="Hey, just checking if you got a chance to look at the proposal.",
        sender="Alex",
        source_app="Gmail",
    )
    assert res.actionable is True
    assert "proposal" in res.task.lower()
    assert res.importance == "high"
