from app.api.routes.health import router as health_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.open_loops import router as open_loops_router
from app.api.routes.reminders import router as reminders_router

__all__ = [
    "health_router",
    "notifications_router",
    "open_loops_router",
    "reminders_router",
]
