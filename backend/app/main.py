import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import text

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.exceptions import CampusOSException
from app.core.logger import configure_logging
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger("campusos.startup")
configure_logging()

# Fail fast in production if critical configuration is missing/insecure.
settings.validate_production()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="CampusOS Backend API",
    docs_url="/docs" if settings.APP_ENV.lower() != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV.lower() != "production" else None,
    openapi_url="/openapi.json" if settings.APP_ENV.lower() != "production" else None,
)

app.add_middleware(CorrelationIdMiddleware)

cors_origins = settings.get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] + cors_origins,
    # Never combine wildcard origins with credentials.
    allow_credentials=("*" not in cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    max_requests_per_minute=settings.RATE_LIMIT_DEFAULT_PER_MINUTE,
)


@app.exception_handler(CampusOSException)
async def campusos_exception_handler(request: Request, exc: CampusOSException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {"code": exc.code, "message": exc.message},
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {"code": "HTTP_ERROR", "message": str(exc.detail)},
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log full detail server-side, but never leak stack traces to clients.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    message = "Internal server error." if settings.APP_ENV.lower() == "production" else str(exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": message},
        },
    )


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
def ensure_database_schema() -> None:
    """Ensure the database is migrated before serving traffic.

    - In non-production, automatically apply Alembic migrations if the schema
      is missing (convenient for local development).
    - In production, never auto-migrate: fail clearly with a 503-style log if
      the schema is absent so operators run migrations explicitly.

    Alembic remains the single source of truth (no create_all()).
    """
    from app.core.database import engine  # local import avoids circulars

    required_tables = {"users", "orders", "payment_intents"}
    try:
        with engine.connect() as conn:
            existing = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
            # For non-SQLite, check information_schema would be needed; SQLite
            # is the supported dev database.
    except Exception as exc:  # pragma: no cover - operational
        logger.error("Database connection failed at startup: %s", exc)
        raise

    if required_tables.issubset(existing):
        return

    if settings.APP_ENV.lower() == "production":
        raise RuntimeError(
            "Database schema is missing. Run 'alembic upgrade head' before "
            "starting the production application."
        )

    # Development: apply migrations automatically and deterministically.
    logger.info("Schema not found; applying Alembic migrations for local development.")
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("Alembic migration failed: %s", result.stderr)
        raise RuntimeError("Failed to apply database migrations.")
    logger.info("Database migrated successfully.")


@app.get("/health", tags=["Health"], summary="Liveness probe")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "mock_blockchain": settings.USE_MOCK_BLOCKCHAIN,
    }


@app.get("/ready", tags=["Health"], summary="Readiness probe")
def readiness_check():
    """Verifies database connectivity without exposing credentials."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ready"}
    except Exception as exc:  # pragma: no cover - operational
        logger.warning("Readiness check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "data": None,
                "error": {"code": "NOT_READY", "message": "Service unavailable."},
            },
        )

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Redirecting...</title>
        //<meta http-equiv="refresh" content="1; url=/docs">
        <style>
            body {
                font-family: system-ui, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: #0f172a;
                color: #e2e8f0;
                text-align: center;
            }
            a {
                color: #38bdf8;
            }
        </style>
    </head>
    <body>
        <div>
            <h2>Redirecting to API Documentation...</h2>
            <p>If you are not redirected automatically, 
               <a href="/docs">click here</a>.</p>
        </div>
    </body>
    </html>
    """
