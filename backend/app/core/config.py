import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _is_prod() -> bool:
    return os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower() in (
        "production",
        "prod",
    )


# Prefix for clearly-insecure development defaults. We never use a real-looking
# secret as a fallback; production must supply real values.
_DEV_JWT_SECRET = "dev-only-insecure-jwt-secret-do-not-use-in-production"


class Settings(BaseSettings):
    PROJECT_NAME: str = "CampusOS Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Runtime environment
    APP_ENV: str = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = APP_ENV  # backwards-compat alias used across the app

    # CORS / public URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    API_URL: str = os.getenv("API_URL", "http://localhost:8000")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{Path(__file__).resolve().parents[3] / 'campusos.db'}"
    )
    
    # Option 2 – absolute path (only for local testing)
    # DATABASE_URL: str = os.getenv(
    #     "DATABASE_URL",
    #     r"sqlite:///C:/Users/Acer/Downloads/CampusOS/backend/campusos.db"
    # )

    # JWT / HMAC secrets. Insecure development default is ONLY used outside
    # production; production requires a real JWT_SECRET (validated at startup).
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY") or os.getenv(
        "JWT_SECRET", _DEV_JWT_SECRET
    )
    JWT_SECRET_KEY_ROTATION: str = os.getenv("JWT_SECRET_KEY_ROTATION", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )

    # Demo / one-click login
    ALLOW_DEMO_LOGIN: bool = os.getenv("ALLOW_DEMO_LOGIN", "false").lower() == "true"

    # Redis rate limiting
    REDIS_URL: str = os.getenv(
        "REDIS_URL", os.getenv("RAILWAY_REDIS_URL", "redis://localhost:6379/0")
    )
    USE_REDIS_RATE_LIMIT: bool = (
        os.getenv("USE_REDIS_RATE_LIMIT", "false").lower() == "true"
    )
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = int(
        os.getenv("RATE_LIMIT_DEFAULT_PER_MINUTE", "100")
    )
    RATE_LIMIT_SENSITIVE_PER_MINUTE: int = int(
        os.getenv("RATE_LIMIT_SENSITIVE_PER_MINUTE", "20")
    )
    RATE_LIMIT_AUTH_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_AUTH_PER_MINUTE", "10"))
    RATE_LIMIT_OTP_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_OTP_PER_MINUTE", "5"))

    # Email OTP / Resend
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    EMAIL_OTP_EXPIRE_SECONDS: int = int(os.getenv("EMAIL_OTP_EXPIRE_SECONDS", "600"))
    EMAIL_OTP_MAX_ATTEMPTS: int = int(os.getenv("EMAIL_OTP_MAX_ATTEMPTS", "3"))
    USE_MOCK_EMAIL_OTP: bool = (
        os.getenv("USE_MOCK_EMAIL_OTP", "true").lower() == "true"
    )

    # Cloudinary (mock when unconfigured)
    CLOUDINARY_CLOUD_NAME: str | None = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY: str | None = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET: str | None = os.getenv("CLOUDINARY_API_SECRET")
    USE_MOCK_CLOUDINARY: bool = (
        os.getenv("USE_MOCK_CLOUDINARY", "true").lower() == "true"
    )

    # Quai blockchain (mock by default)
    QUAI_RPC_URL: str = os.getenv("QUAI_RPC_URL", "")
    QUAI_CONTRACT_ADDRESS: str = os.getenv("QUAI_CONTRACT_ADDRESS", "")
    QUAI_ESCROW_CONTRACT_ADDRESS: str = os.getenv("QUAI_ESCROW_CONTRACT_ADDRESS", "")
    QUAI_PRIVATE_KEY: str = os.getenv("QUAI_PRIVATE_KEY", "")
    QUAI_CHAIN_ID: int = int(os.getenv("QUAI_CHAIN_ID", "0") or "0")
    QUAI_NETWORK: str = os.getenv("QUAI_NETWORK", "")
    QUAI_RPC_TIMEOUT: int = int(os.getenv("QUAI_RPC_TIMEOUT", "30"))
    QUAI_TX_TIMEOUT: int = int(os.getenv("QUAI_TX_TIMEOUT", "120"))
    USE_MOCK_BLOCKCHAIN: bool = (
        os.getenv("USE_MOCK_BLOCKCHAIN", "true").lower() == "true"
    )
    # Explicit acknowledgement that mock mode is acceptable in production.
    ALLOW_MOCK_BLOCKCHAIN_IN_PRODUCTION: bool = (
        os.getenv("ALLOW_MOCK_BLOCKCHAIN_IN_PRODUCTION", "false").lower() == "true"
    )

    # Campus Identity QR HMAC secret
    QR_SECRET_KEY: str = os.getenv("QR_SECRET_KEY") or os.getenv(
        "JWT_SECRET_KEY", _DEV_JWT_SECRET
    )

    # Blip Pay
    BLIP_API_URL: str = os.getenv("BLIP_API_URL", "")
    BLIP_PAY_API_KEY: str = os.getenv("BLIP_PAY_API_KEY", "")
    # In non-production a dev-only secret allows HMAC verification to work;
    # production must supply BLIP_PAY_WEBHOOK_SECRET (validated at startup).
    BLIP_PAY_WEBHOOK_SECRET: str = os.getenv(
        "BLIP_PAY_WEBHOOK_SECRET",
        os.getenv(
            "BLIP_WEBHOOK_SECRET",
            "dev-only-insecure-webhook-secret",
        ),
    )
    BLIP_PAY_WEBHOOK_SECRET_ROTATION: str = os.getenv(
        "BLIP_PAY_WEBHOOK_SECRET_ROTATION", ""
    )
    USE_MOCK_BLIP_PAY: bool = (
        os.getenv("USE_MOCK_BLIP_PAY", "true").lower() == "true"
    )

    # Uploads
    MAX_UPLOAD_SIZE: int = int(
        os.getenv("MAX_UPLOAD_SIZE", str(5 * 1024 * 1024))
    )
    ALLOWED_FILE_TYPES: set[str] = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    def get_jwt_secret_keys(self) -> list[str]:
        keys = [self.JWT_SECRET_KEY]
        if self.JWT_SECRET_KEY_ROTATION:
            keys.extend(
                k.strip()
                for k in self.JWT_SECRET_KEY_ROTATION.split(",")
                if k.strip()
            )
        return list(dict.fromkeys(keys))

    def get_blip_webhook_secrets(self) -> list[str]:
        if not self.BLIP_PAY_WEBHOOK_SECRET:
            return []
        secrets = [self.BLIP_PAY_WEBHOOK_SECRET]
        if self.BLIP_PAY_WEBHOOK_SECRET_ROTATION:
            secrets.extend(
                s.strip()
                for s in self.BLIP_PAY_WEBHOOK_SECRET_ROTATION.split(",")
                if s.strip()
            )
        return list(dict.fromkeys(secrets))

    @staticmethod
    def _csv(value) -> list[str]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(v).strip() for v in value if str(v).strip()]
        return [v.strip() for v in str(value).split(",") if v.strip()]

    @property
    def _env(self) -> str:
        # ENVIRONMENT is retained for backward compatibility with older
        # tests/code; prefer whichever is explicitly set.
        return (self.ENVIRONMENT or self.APP_ENV or "development").lower()

    def get_cors_origins(self) -> list[str]:
        custom = self._csv(self.CORS_ORIGINS)
        if self._env in ("production", "prod"):
            allow = {
                "https://campusos.vercel.app",
                "https://campusos.ng",
                "https://www.campusos.ng",
            }
            if self.FRONTEND_URL and self.FRONTEND_URL.startswith("https://"):
                allow.add(self.FRONTEND_URL)
            allow.update(o for o in custom if o.startswith("https://") and o != "*")
            return sorted(allow)
        dev = {
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        }
        if self.FRONTEND_URL:
            dev.add(self.FRONTEND_URL)
        dev.update(custom)
        return sorted(dev)

    def validate_production(self) -> None:
        """Fail fast when production is missing critical configuration."""
        if self._env not in ("production", "prod"):
            return
        errors: list[str] = []
        if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == _DEV_JWT_SECRET:
            errors.append("JWT_SECRET_KEY must be set to a strong, unique value.")
        if (
            not self.BLIP_PAY_WEBHOOK_SECRET
            or self.BLIP_PAY_WEBHOOK_SECRET == "dev-only-insecure-webhook-secret"
        ):
            errors.append("BLIP_PAY_WEBHOOK_SECRET must be set to a real value in production.")
        if not self.QR_SECRET_KEY or self.QR_SECRET_KEY == _DEV_JWT_SECRET:
            errors.append("QR_SECRET_KEY must be set in production.")
        if self.USE_MOCK_BLOCKCHAIN and not self.ALLOW_MOCK_BLOCKCHAIN_IN_PRODUCTION:
            errors.append(
                "USE_MOCK_BLOCKCHAIN is enabled in production. Set "
                "ALLOW_MOCK_BLOCKCHAIN_IN_PRODUCTION=true only if this is intentional."
            )
        if self.ALLOW_DEMO_LOGIN:
            errors.append("ALLOW_DEMO_LOGIN must be disabled in production.")
        if "*" in self.CORS_ORIGINS:
            errors.append("CORS_ORIGINS must not contain '*' in production.")
        if self.USE_MOCK_BLIP_PAY:
            errors.append("USE_MOCK_BLIP_PAY must be disabled in production.")
        if not self.USE_MOCK_BLIP_PAY and not (self.BLIP_API_URL and self.BLIP_PAY_API_KEY):
            errors.append(
                "Live Blip mode requires BLIP_API_URL and BLIP_PAY_API_KEY."
            )
        if errors:
            raise RuntimeError(
                "Production configuration errors:\n- " + "\n- ".join(errors)
            )

    def validate_production_secrets(self) -> dict[str, bool]:
        """Backwards-compatible alias for validate_production().

        Raises ValueError when production uses insecure defaults, matching the
        original contract used by existing tests.
        """
        insecure: list[str] = []
        if self.JWT_SECRET_KEY == _DEV_JWT_SECRET:
            insecure.append("JWT_SECRET_KEY")
        if not self.BLIP_PAY_WEBHOOK_SECRET:
            insecure.append("BLIP_PAY_WEBHOOK_SECRET")
        if self._env in ("production", "prod"):
            if insecure or self.USE_MOCK_BLOCKCHAIN or self.ALLOW_DEMO_LOGIN:
                raise ValueError(
                    "CRITICAL: Insecure default secrets detected in production"
                )
        return {"insecure_defaults": bool(insecure)}

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
