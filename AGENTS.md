# OpenLoop AI Backend — Agent Guidelines & Context

## Project Overview
This repository contains the production FastAPI backend for **OpenLoop AI** — an AI-driven notification assistant that captures Android system notifications, extracts actionable tasks/obligations, deduplicates follow-ups, and schedules reminders.

## Tech Stack & Tooling
- **Language**: Python 3.12+
- **Package & Task Runner**: `uv` (always use `uv run ...`)
- **Web**: FastAPI + Pydantic v2
- **ORM & DB**: SQLAlchemy 2.x async with `asyncpg` on PostgreSQL / SQLite for tests
- **Migrations**: Alembic (`alembic upgrade head`)
- **Tests**: `pytest` (`uv run pytest`)

## Key Rules & Architectural Principles
1. **Timezone Storage**: All timestamps (`deadline`, `scheduled_for`, `received_at`, `created_at`) MUST be stored in **UTC** with timezone awareness. User-specific calculations use `User.timezone` via `DateService`.
2. **Deduplication Priority**: Follow-up notifications for open tasks must update existing `OpenLoop` records rather than creating duplicates (managed by `OpenLoopService.process_actionable_notification`).
3. **Non-Blocking Ingestion**: Notification ingestion (`POST /api/v1/notifications`) must return `HTTP 202 Accepted` within 15ms. Heavy AI analysis runs in FastAPI `BackgroundTasks`.
4. **Idempotency**: Notification events are deduplicated by `(user_id, device_id, client_event_id)`.
5. **Always Run Tests**: After making changes, run `uv run pytest` to ensure all test suites pass.

## Custom Skill Reference
For detailed domain model references, pipeline architecture, and API schemas, activate the skill:
- `.agents/skills/openloop-backend/SKILL.md`
