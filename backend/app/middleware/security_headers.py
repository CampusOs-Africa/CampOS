from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    OWASP HTTP Security Headers Middleware.
    Enforces strict security headers on all FastAPI responses to mitigate XSS, CSRF, Clickjacking, and MIME-sniffing.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        # HSTS is only meaningful over HTTPS.
        from app.core.config import settings as _settings

        if _settings.APP_ENV.lower() == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        response.headers["Content-Security-Policy"] = (
    "default-src 'self' "
    "'unsafe-inline' "
    "'unsafe-eval' "
    "https://cdn.jsdelivr.net "
    "https://res.cloudinary.com "
    "https://rpc.quai.network "
    "https://testnet.quaiscan.io; "
    "img-src 'self' data: "
    "https://res.cloudinary.com "
    "https://fastapi.tiangolo.com;"
)
        return response
