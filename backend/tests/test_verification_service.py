import io

import pytest
from fastapi import UploadFile

from app.core.exceptions import (
    DuplicateSubmissionError,
    EmailValidationError,
    ForbiddenError,
)
from app.models.user import User
from app.services.verification_service import (
    VerificationService,
    validate_university_email,
)


def test_university_email_validation():
    # Valid domains
    assert validate_university_email("student@unijos.edu.ng") == "student@unijos.edu.ng"
    assert validate_university_email("amina.bello@ui.edu.ng") == "amina.bello@ui.edu.ng"
    assert validate_university_email("john.doe@mit.edu") == "john.doe@mit.edu"

    # Invalid domain
    with pytest.raises(EmailValidationError):
        validate_university_email("student@gmail.com")
    with pytest.raises(EmailValidationError):
        validate_university_email("student@yahoo.co.uk")


@pytest.mark.asyncio
async def test_verification_service_flow(db_session):
    # Setup test user and admin
    student = User(id="student-1", name="Amina Bello", email="amina@test.org", role="student", trust_score=50)
    admin = User(id="admin-1", name="Prof. Adebayo", email="adebayo@test.org", role="admin", trust_score=100)
    db_session.add(student)
    db_session.add(admin)
    db_session.commit()

    service = VerificationService(db=db_session)

    # 1. Submit verification
    id_file = UploadFile(
        filename="id.pdf",
        file=io.BytesIO(b"%PDF-1.4 id content"),
        headers={"content-type": "application/pdf"},
    )
    letter_file = UploadFile(
        filename="letter.pdf",
        file=io.BytesIO(b"%PDF-1.4 letter content"),
        headers={"content-type": "application/pdf"},
    )

    verif = await service.submit_verification(
        user_id="student-1",
        university_email="amina.bello@unijos.edu.ng",
        student_id_file=id_file,
        admission_letter_file=letter_file,
    )
    assert verif.status == "pending"
    assert verif.user_id == "student-1"
    assert ".pdf" in verif.student_id_url
    assert "campusos/student_ids" in verif.student_id_url
    assert ".pdf" in verif.admission_letter_url
    assert "campusos/admission_letters" in verif.admission_letter_url

    # Check status endpoint logic
    status = service.get_verification_status("student-1")
    assert status["verification_status"] == "pending"
    assert status["trust_score"] == 50
    assert status["credential_hash"] is None

    # 2. Check duplicate submission prevention
    with pytest.raises(DuplicateSubmissionError):
        id_file2 = UploadFile(
            filename="id2.pdf",
            file=io.BytesIO(b"id2 content"),
            headers={"content-type": "application/pdf"},
        )
        letter_file2 = UploadFile(
            filename="letter2.pdf",
            file=io.BytesIO(b"letter2 content"),
            headers={"content-type": "application/pdf"},
        )
        await service.submit_verification(
            user_id="student-1",
            university_email="amina.bello@unijos.edu.ng",
            student_id_file=id_file2,
            admission_letter_file=letter_file2,
        )

    # 3. Admin approve verification (asynchronously via QuaiBlockchainService)
    approved = await service.admin_approve_verification(admin_id="admin-1", verification_id=verif.id)
    assert approved.status == "approved"
    assert approved.approved_by == "admin-1"
    assert approved.credential_hash is not None
    assert len(approved.credential_hash) == 64
    assert approved.tx_hash is not None
    assert "0xquai_" in approved.tx_hash

    # Check user trust score (+10) and verification status
    db_session.refresh(student)
    assert student.verification_status == "verified"
    assert student.trust_score == 60  # 50 + 10

    # 4. Check verification history log
    history = service.get_verification_history("student-1")
    assert len(history) == 2
    assert history[0].new_status == "approved"
    assert history[1].new_status == "pending"


@pytest.mark.asyncio
async def test_admin_permissions(db_session):
    student1 = User(id="s1", name="Student 1", email="s1@test.org", role="student")
    student2 = User(id="s2", name="Student 2", email="s2@test.org", role="student")
    db_session.add(student1)
    db_session.add(student2)
    db_session.commit()

    service = VerificationService(db=db_session)
    with pytest.raises(ForbiddenError):
        await service.admin_approve_verification(admin_id="s1", verification_id="fake-id")
