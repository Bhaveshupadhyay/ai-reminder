from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.logging import logger

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Service Health Check",
    description="Returns overall health status of the application.",
    status_code=status.HTTP_200_OK,
)
async def health_check():
    return {"status": "ok"}


@router.get(
    "/health/db",
    summary="Database Connectivity Check",
    description="Verifies async PostgreSQL database connectivity with a ping query.",
    status_code=status.HTTP_200_OK,
)
async def health_db_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "disconnected", "detail": str(e)},
        )
