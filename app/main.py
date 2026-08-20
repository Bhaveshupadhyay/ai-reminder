from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.health import router as health_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.open_loops import router as open_loops_router
from app.api.routes.reminders import router as reminders_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info(
        f"Starting {settings.PROJECT_NAME} in [{settings.ENVIRONMENT}] mode. AI_PROVIDER={settings.AI_PROVIDER}"
    )
    yield
    # Shutdown
    logger.info("Shutting down application...")


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="""
# AI Open-Loop Reminder Backend API

Intelligently analyzes captured smartphone notifications (WhatsApp, Slack, Gmail, etc.),
detects actionable open loops (tasks, obligations, follow-ups), extracts structured metadata,
and manages proactive reminders.

## Features
* **Async Ingestion**: Non-blocking ingestion with FastAPI background processing
* **Structured AI Extraction**: Pydantic v2 validation of task, person, deadline, confidence
* **Smart Deduplication**: Automatically associates follow-up messages with existing open loops
* **Temporal Normalization**: Normalizes relative deadlines ('tomorrow', 'Friday', 'after 6') to UTC based on user timezone
* **Idempotent**: Client event deduplication
* **Pluggable AI**: Seamless Mock, OpenAI, and Gemini providers
        """,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Exception Handlers
    register_exception_handlers(app)

    # Register Routes
    # Health checks at root level
    app.include_router(health_router)

    # API v1 endpoints
    app.include_router(notifications_router, prefix=settings.API_V1_STR)
    app.include_router(open_loops_router, prefix=settings.API_V1_STR)
    app.include_router(reminders_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
