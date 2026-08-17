import os
import re
import uuid

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import FileValidationError


def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filenames by stripping directory traversal sequences and null bytes."""
    clean = os.path.basename(filename).replace("\x00", "")
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", clean)
    return clean or "unnamed_file"


class StorageService:
    def __init__(self):
        if (
            not settings.USE_MOCK_CLOUDINARY
            and settings.CLOUDINARY_API_KEY != "mock_key"
        ):
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True,
            )

    async def validate_file(
        self, file: UploadFile, max_size_bytes: int | None = None
    ) -> None:
        if not file:
            raise FileValidationError("No file uploaded.")

        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            allowed = ", ".join(settings.ALLOWED_FILE_TYPES)
            raise FileValidationError(
                f"Invalid file type '{file.content_type}'. Allowed types: {allowed}."
            )

        max_bytes = max_size_bytes or settings.MAX_UPLOAD_SIZE
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        if size > max_bytes:
            max_mb = max_bytes / (1024 * 1024)
            raise FileValidationError(
                f"File '{file.filename}' size ({size / (1024 * 1024):.2f} MB) exceeds maximum allowed size of {max_mb:.1f} MB."
            )

        # OWASP Magic Bytes (File Header Signature) Verification against MIME-spoofing
        header = await file.read(8)
        await file.seek(0)

        is_pdf = header.startswith(b"%PDF-")
        is_jpeg = header.startswith(b"\xff\xd8\xff")
        is_png = header.startswith(b"\x89PNG\r\n\x1a\n")
        is_webp = header.startswith(b"RIFF") and b"WEBP" in header

        if not (is_pdf or is_jpeg or is_png or is_webp):
            raise FileValidationError(
                f"File '{file.filename}' header signature (magic bytes) does not match allowed PDF or image format. Spoofed or malicious file detected."
            )

    async def upload_file(
        self, file: UploadFile, folder: str = "campusos/verifications"
    ) -> str:
        await self.validate_file(file)
        safe_filename = sanitize_filename(file.filename or "upload.jpg")

        if settings.USE_MOCK_CLOUDINARY or not settings.CLOUDINARY_API_KEY:
            # Local/mock storage: return an obviously non-production URL so the
            # UI/admin never mistakes a placeholder for a real Cloudinary file.
            file_id = uuid.uuid4().hex[:12]
            ext = safe_filename.split(".")[-1] if "." in safe_filename else "jpg"
            return f"mock-storage://{folder}/{file_id}.{ext}"

        content = await file.read()
        res = cloudinary.uploader.upload(
            content,
            folder=folder,
            resource_type="auto",
        )
        return res.get("secure_url")
