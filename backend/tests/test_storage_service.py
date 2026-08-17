import io

import pytest
from fastapi import UploadFile

from app.core.exceptions import FileValidationError
from app.services.storage_service import StorageService


@pytest.mark.asyncio
async def test_valid_file_upload():
    service = StorageService()
    file_content = b"%PDF-1.4 mock pdf content"
    upload_file = UploadFile(filename="student_id.pdf", file=io.BytesIO(file_content), headers={"content-type": "application/pdf"})
    
    url = await service.upload_file(upload_file, folder="test/verifications")
    assert url.startswith("mock-storage://")
    assert "test/verifications" in url
    assert url.endswith(".pdf")

@pytest.mark.asyncio
async def test_invalid_file_type():
    service = StorageService()
    file_content = b"executable binary"
    upload_file = UploadFile(filename="malicious.exe", file=io.BytesIO(file_content), headers={"content-type": "application/x-msdownload"})
    
    with pytest.raises(FileValidationError) as exc_info:
        await service.upload_file(upload_file)
    assert "Invalid file type" in str(exc_info.value)

@pytest.mark.asyncio
async def test_file_too_large():
    service = StorageService()
    # Create a dummy 6MB file in memory
    large_content = b"a" * (6 * 1024 * 1024)
    upload_file = UploadFile(filename="oversized.pdf", file=io.BytesIO(large_content), headers={"content-type": "application/pdf"})
    
    with pytest.raises(FileValidationError) as exc_info:
        await service.upload_file(upload_file)
    assert "exceeds maximum allowed size" in str(exc_info.value)
