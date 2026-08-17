"""Payment provider abstraction.

Concrete providers encapsulate all external payment communication. The rest of
the application depends only on this interface, so Blip-specific HTTP never
leaks into routers/services.
"""

from __future__ import annotations

import abc
import hashlib
import hmac
import logging
from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.core.exceptions import CampusOSException

logger = logging.getLogger("campusos.payments")


@dataclass
class ProviderPayment:
    provider_reference: str | None
    checkout_url: str | None
    status: str  # provider-normalized status
    raw: dict[str, Any] | None = None


@dataclass
class WebhookEvent:
    event_id: str
    event_type: str | None
    payment_reference: str | None
    status: str | None
    amount_minor: int | None
    currency: str | None
    raw: dict[str, Any]


class PaymentProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def create_payment(
        self, *, reference: str, amount_minor: int, currency: str, buyer_email: str | None
    ) -> ProviderPayment: ...

    @abc.abstractmethod
    def parse_webhook(
        self, *, headers: dict[str, str], raw_body: bytes
    ) -> WebhookEvent: ...

    def verify_webhook_signature(
        self, headers: dict[str, str], raw_body: bytes
    ) -> bool:
        """Verify the provider webhook signature. Default: HMAC-SHA256."""
        raise NotImplementedError


class BlipPayProvider(PaymentProvider):
    """Blip Pay adapter.

    NOTE ON LIVE INTEGRATION: The exact Blip Pay HTTP contract (base URL, auth
    scheme, create-payment request/response, webhook event format and status
    values) could NOT be verified from this repository or available
    documentation. The live HTTP path is therefore deliberately BLOCKED until
    the provider contract and credentials are supplied. In mock mode it returns
    deterministic, clearly-labelled fake data for development/testing.
    """

    name = "blip_pay"
    LIVE_BLOCKED_REASON = (
        "Blip Pay live integration is not configured: the provider API contract "
        "and credentials have not been verified. Set USE_MOCK_BLIP_PAY=true for "
        "development."
    )

    def __init__(self) -> None:
        self.mock = settings.USE_MOCK_BLIP_PAY
        self.api_url = (settings.BLIP_API_URL or "").rstrip("/")
        self.api_key = settings.BLIP_PAY_API_KEY

    # ---------------------------------------------------------- create payment
    def create_payment(
        self,
        *,
        reference: str,
        amount_minor: int,
        currency: str,
        buyer_email: str | None,
    ) -> ProviderPayment:
        if self.mock:
            # Deterministic fake checkout URL for local development only.
            logger.info("[MOCK-BLIP] Created payment intent reference=%s", reference)
            return ProviderPayment(
                provider_reference=reference,
                checkout_url=f"{settings.FRONTEND_URL}/checkout/{reference}",
                status="pending",
                raw={"mock": True, "reference": reference},
            )

        # Live path intentionally disabled: do not fabricate a request to an
        # unverified endpoint.
        raise CampusOSException(self.LIVE_BLOCKED_REASON, status_code=501)

    # ----------------------------------------------------------------- webhook
    def _header(self, headers: dict[str, str], *names: str) -> str | None:
        lower = {k.lower(): v for k, v in headers.items()}
        for n in names:
            if n.lower() in lower:
                return lower[n.lower()]
        return None

    def verify_webhook_signature(
        self, headers: dict[str, str], raw_body: bytes
    ) -> bool:
        if self.mock:
            sig = self._header(headers, "x-blip-signature")
            # Mock test harness signs with the dev secret; accept mock_sig* too.
            if sig and sig.startswith("mock_sig"):
                return True
        secret = settings.BLIP_PAY_WEBHOOK_SECRET
        if not secret:
            return False
        sig = self._header(headers, "x-blip-signature", "x-blik-signature")
        if not sig:
            return False
        expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, sig)

    def parse_webhook(
        self, *, headers: dict[str, str], raw_body: bytes
    ) -> WebhookEvent:
        if not self.verify_webhook_signature(headers, raw_body):
            raise CampusOSException("Invalid webhook signature.", status_code=401)

        import json

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as e:
            raise CampusOSException("Malformed webhook payload.", status_code=400) from e

        # Until the real Blip event schema is verified, only the fields we
        # already use in the HMAC-signed payload are trusted.
        reference = payload.get("payment_reference") or payload.get("reference")
        status = payload.get("status")
        event_id = (
            payload.get("event_id")
            or payload.get("id")
            or hashlib.sha256(raw_body).hexdigest()
        )
        amount = payload.get("amount_minor")
        if amount is None and "amount" in payload:
            # If a major-unit amount is supplied, never trust it for money
            # movement without provider verification; leave None to force a
            # server-side check.
            amount = None

        return WebhookEvent(
            event_id=str(event_id),
            event_type=payload.get("event"),
            payment_reference=reference,
            status=str(status).lower() if status else None,
            amount_minor=int(amount) if amount is not None else None,
            currency=payload.get("currency"),
            raw=payload,
        )


def get_provider() -> PaymentProvider:
    """Factory for the active payment provider."""
    return BlipPayProvider()


def to_minor(amount: float, currency: str = "NGN") -> int:
    """Convert a major-unit amount to integer minor units (no float money math)."""
    # NGN uses 2 minor units (kobo). Centralize decimals per currency here.
    decimals = 2
    return int(round(amount * (10**decimals)))


def from_minor(amount_minor: int, currency: str = "NGN") -> float:
    decimals = 2
    return amount_minor / (10**decimals)
