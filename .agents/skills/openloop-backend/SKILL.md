---
name: openloop-backend
description: Comprehensive architectural guide, domain model reference, API catalog, deduplication mechanics, timezone normalization runbook, testing strategies, and deployment runbook for the AI Open-Loop Reminder Backend. Activate whenever modifying, querying, debugging, or extending this codebase.
---

# OpenLoop Backend Architectural Guide & Developer Runbook

## Overview
OpenLoop Backend is a lightweight, high-performance async Python backend for capturing incoming smartphone notifications (WhatsApp, Slack, Gmail, SMS, etc.), detecting actionable obligations ("open loops"), extracting structured metadata (task, person, deadline, importance, confidence), deduplicating follow-ups, and scheduling proactive reminders.

---

## 🏗️ Core Architecture & Tech Stack

- **Runtime**: Python 3.12+ (managed with `uv`)
- **Web Framework**: FastAPI (with `fastapi[standard]`)
- **Database**: PostgreSQL with async driver `asyncpg` (SQLAlchemy 2.x async ORM)
- **Migrations**: Alembic with async migration runner (`alembic/env.py`)
- **Validation**: Pydantic v2
- **Testing**: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` (in-memory SQLite `StaticPool` for instant test runs)
- **Deployment**: Multi-stage `Dockerfile`, GitHub Actions CI/CD to **Render.com** (`.github/workflows/render-deploy.yml`), `render.yaml`

---

## 📁 Repository Structure

```text
open-loop-backend/
├── alembic/                      # Database migrations
│   ├── versions/                 # Revision scripts (001_initial_schema.py)
│   └── env.py                    # Async migration runner with Supabase pooler support
├── app/
│   ├── api/
│   │   ├── dependencies.py       # FastAPI DB session & pagination dependency injections
│   │   └── routes/
│   │       ├── health.py         # GET & HEAD /health and /health/db probes
│   │       ├── notifications.py  # Ingestion & event lookup
│   │       ├── open_loops.py     # OpenLoop lifecycle (list, patch, complete, dismiss)
│   │       └── reminders.py      # Reminders CRUD and cancel
│   ├── core/
│   │   ├── config.py             # Pydantic Settings (.env configuration)
│   │   ├── database.py           # Async SQLAlchemy engine with connection pool & pooler settings
│   │   ├── exceptions.py         # App exceptions & FastAPI exception handlers
│   │   └── logging.py            # Structured JSON / console logger
│   ├── models/                   # SQLAlchemy ORM models (GUID cross-platform PKs)
│   │   ├── base.py               # GUID type decorator & TimestampMixin
│   │   ├── user.py               # User account & timezone holder
│   │   ├── device.py             # Client smartphone registration
│   │   ├── notification_event.py # Immutable raw notification audit log
│   │   ├── open_loop.py          # Actionable obligation entity
│   │   └── reminder.py           # Scheduled trigger entity
│   ├── repositories/             # Data access repository pattern
│   ├── schemas/                  # Pydantic v2 DTOs (AI output, events, loops, reminders)
│   ├── scripts/
│   │   └── seed.py               # Demo database seeder script
│   └── services/
│       ├── ai/                   # AI Provider interface (Mock, OpenAI, Gemini)
│       ├── date_service.py       # Relative date parser & UTC normalizer
│       ├── filter_service.py     # Fast regex & package ignore heuristics (OTPs, spam)
│       ├── notification_service.py # Non-blocking background ingestion pipeline
│       ├── open_loop_service.py  # Smart deduplication & lifecycle manager
│       └── reminder_service.py   # Scheduled reminder generator
├── tests/                        # 29+ unit & integration tests
├── .github/workflows/            # CI & Render deployment
├── Dockerfile                    # Multi-stage container with dynamic $PORT binding
├── render.yaml                   # Render Blueprint IaC
├── pyproject.toml                # uv project dependencies
└── main.py                       # Application entrypoint
```

---

## 🗄️ Database Schema & Domain Model

1. **`User`** (`users`):
   - Fields: `id` (UUID), `timezone` (String, e.g. `"Asia/Kolkata"` or `"UTC"`), `created_at`, `updated_at`.
   - **Crucial**: Holds the user's local timezone used by `DateService` to compute absolute UTC datetimes from relative texts like *"tomorrow at 5pm"* or *"lets do meeting at 6pm"*.

2. **`Device`** (`devices`):
   - Fields: `id` (UUID), `user_id` (FK), `platform` (`"android"`), `device_name`, `last_seen_at`.

3. **`NotificationEvent`** (`notification_events`):
   - Fields: `id` (UUID), `user_id`, `device_id`, `client_event_id`, `source_app`, `source_package`, `sender`, `title`, `body`, `received_at`, `processing_status` (`pending`, `processing`, `processed`, `ignored`, `failed`), `processing_error`, `ai_result` (JSONB).
   - **Idempotency**: Unique constraint on `(user_id, device_id, client_event_id)` prevents duplicate processing on client retries.

4. **`OpenLoop`** (`open_loops`):
   - Fields: `id` (UUID), `user_id`, `source_notification_id` (FK), `task`, `person`, `deadline` (UTC), `deadline_text`, `importance` (`low`, `medium`, `high`), `confidence` (float), `reason`, `status` (`open`, `completed`, `dismissed`, `snoozed`), `completed_at`.

5. **`Reminder`** (`reminders`):
   - Fields: `id` (UUID), `user_id`, `open_loop_id` (FK), `scheduled_for` (UTC), `status` (`scheduled`, `triggered`, `cancelled`), `triggered_at`.

---

## ⚙️ Ingestion & Processing Pipeline

1. **Phase 1: Ingestion (<15ms)**:
   - `POST /api/v1/notifications` validates payload and inserts `NotificationEvent` (`status="processing"`).
   - Dispatches FastAPI `BackgroundTasks.add_task(process_notification)`.
   - Returns `HTTP 202 Accepted` immediately without blocking for the LLM.

2. **Phase 2: Cheap Heuristic Filtering (`FilterService`)**:
   - Skips system UI packages (`com.android.systemui`, `com.android.vending`, etc.).
   - Regex matches OTPs (`"Your verification code is 123456"`), battery/system alerts, promotional sales.
   - If matched: marks `NotificationEvent` as `"ignored"` and terminates pipeline.

3. **Phase 3: AI Extraction (`AIProvider`)**:
   - Supports `MockAIProvider`, `OpenAIProvider`, and `GeminiProvider`.
   - Returns `OpenLoopAnalysis(actionable, task, person, deadline, deadline_text, importance, confidence, reason)`.

4. **Phase 4: Timezone Normalization (`DateService`)**:
   - Resolves `"tomorrow"`, `"at 6pm"`, `"after 6"`, `"in 2 hours"`, `"next week"`, etc.
   - Combines with `User.timezone` to compute absolute UTC timestamps for storage.

5. **Phase 5: Smart Deduplication (`OpenLoopService`)**:
   - Evaluates active open loops (`status = 'open'` within 14-day window).
   - **Scoring formula**: Person Match ($+0.25$) + Token Jaccard ($+0.65 \times \text{Sim}$) + Key Concept Overlap ($+0.30$).
   - If $\text{Score} \ge 0.55$: Updates existing loop (`updated_at = NOW()`, updates source notification, refreshes deadline, escalates importance, appends follow-up reason).
   - If $\text{Score} < 0.55$: Inserts a new `OpenLoop`.

6. **Phase 6: Reminder Scheduling (`ReminderService`)**:
   - If `deadline` is present, inserts a `Reminder` with `status="scheduled"`.

---

## 🌐 API Reference Catalog

| Method | Route | Description |
| :--- | :--- | :--- |
| `GET`, `HEAD` | `/health`, `/api/v1/health` | Service health probe |
| `GET`, `HEAD` | `/health/db`, `/api/v1/health/db` | Database connectivity probe |
| `POST` | `/api/v1/notifications` | Ingest notification event (idempotent, returns 202) |
| `GET` | `/api/v1/notifications/{id}` | Get single notification event with AI output |
| `GET` | `/api/v1/notifications` | List notifications (filters: `user_id`, `source_app`, `processing_status`) |
| `GET` | `/api/v1/open-loops` | List open loops (filters: `user_id`, `status`, pagination) |
| `GET` | `/api/v1/open-loops/{id}` | Get single open loop details |
| `PATCH` | `/api/v1/open-loops/{id}` | Update open loop (`task`, `deadline`, `importance`, `status`) |
| `POST` | `/api/v1/open-loops/{id}/complete` | Mark open loop completed (sets `completed_at`) |
| `POST` | `/api/v1/open-loops/{id}/dismiss` | Dismiss open loop |
| `POST` | `/api/v1/reminders` | Create manual reminder |
| `GET` | `/api/v1/reminders` | List reminders (filters: `user_id`, `status`, `open_loop_id`) |
| `PATCH` | `/api/v1/reminders/{id}` | Update reminder schedule or status |
| `POST` | `/api/v1/reminders/{id}/cancel` | Cancel scheduled reminder |

---

## 🛠️ Developer Runbook & Commands

### Running Locally
```bash
# Start development server with hot-reload
uv run fastapi dev

# Run automated test suite with coverage
uv run pytest --cov=app --cov-report=term-missing

# Apply database migrations
uv run alembic upgrade head

# Seed demo dataset
uv run python -m app.scripts.seed

# Query codebase knowledge graph via Graphify
uv run graphify query "How does notification deduplication work?"
```

### Timezone Guidelines
- When debugging reminders or deadlines, always check the `User.timezone` field in PostgreSQL.
- Database timestamps (`received_at`, `created_at`, `deadline`, `scheduled_for`) are ALWAYS stored in **UTC**.
- Clients must convert UTC datetimes to the user's local timezone for display.

### Supabase / PgBouncer Notes
- Default database name on Supabase is `/postgres`.
- With transaction poolers (`*.pooler.supabase.com:6543`), prepared statement caching is disabled via `statement_cache_size = 0` in `app/core/database.py` and `alembic/env.py`.
