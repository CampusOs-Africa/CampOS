import io
from datetime import timedelta

import pytest
from fastapi import UploadFile

from app.core.exceptions import CampusOSException, FileValidationError, ForbiddenError
from app.core.security import (
    check_role_permission,
    create_access_token,
    hash_secret,
    verify_access_token,
    verify_secret,
)
from app.services.storage_service import StorageService, sanitize_filename


def test_jwt_access_token_creation_and_verification():
    token = create_access_token(subject="user-uuid-123", role="admin")
    payload = verify_access_token(token)
    assert payload["sub"] == "user-uuid-123"
    assert payload["role"] == "admin"
    assert payload["iss"] == "CampusOS-Auth-Engine"

    # Verify invalid signature rejection
    tampered = token[:-5] + "aaaaa"
    with pytest.raises(CampusOSException) as exc_info:
        verify_access_token(tampered)
    assert exc_info.value.status_code == 401
    assert "Invalid JWT access token" in exc_info.value.message

    # Verify expired token rejection
    expired_token = create_access_token(
        subject="user-uuid-123",
        role="student",
        expires_delta=timedelta(seconds=-10)
    )
    with pytest.raises(CampusOSException) as exc_info:
        verify_access_token(expired_token)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.message


def test_secret_hashing_and_verification():
    secret = "my-super-secret-password"
    hashed = hash_secret(secret)
    assert verify_secret(secret, hashed) is True
    assert verify_secret("wrong-password", hashed) is False


def test_role_permission_enforcement():
    # Student cannot perform admin action
    with pytest.raises(ForbiddenError):
        check_role_permission("student", ["admin"])

    # Admin can perform admin action
    check_role_permission("admin", ["admin", "merchant"])


def test_filename_sanitization():
    assert sanitize_filename("../../etc/passwd.jpg") == "passwd.jpg"
    assert sanitize_filename("valid_photo.png") == "valid_photo.png"
    assert sanitize_filename("null\x00byte.pdf") == "nullbyte.pdf"


@pytest.mark.asyncio
async def test_magic_bytes_validation_rejection():
    service = StorageService()

    # Spoofed file: .pdf extension and application/pdf mime type, but starts with malicious script header
    fake_content = b"#!/bin/bash\necho 'malicious'"
    spoofed_file = UploadFile(
        filename="spoofed.pdf",
        file=io.BytesIO(fake_content),
        headers={"content-type": "application/pdf"}
    )

    with pytest.raises(FileValidationError) as exc_info:
        await service.validate_file(spoofed_file)
    assert "header signature (magic bytes) does not match" in str(exc_info.value)


def test_owasp_security_headers_on_response(client):
    response = client.get("/health")
    assert response.status_code == 200
    headers = response.headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    # HSTS is only sent in production (HTTPS)
    assert "Referrer-Policy" in headers
    assert "Content-Security-Policy" in headers
    assert "camera=()" in headers["Permissions-Policy"]
