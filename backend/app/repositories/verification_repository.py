
from sqlalchemy.orm import Session

from app.models.verification import StudentVerification, VerificationHistory


class VerificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, verification: StudentVerification) -> StudentVerification:
        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)
        return verification

    def get_by_id(self, verification_id: str) -> StudentVerification | None:
        return self.db.query(StudentVerification).filter(StudentVerification.id == verification_id).first()

    def get_by_user_id(self, user_id: str) -> StudentVerification | None:
        return (
            self.db.query(StudentVerification)
            .filter(StudentVerification.user_id == user_id)
            .order_by(StudentVerification.created_at.desc())
            .first()
        )

    def get_active_by_user_id(self, user_id: str) -> StudentVerification | None:
        return (
            self.db.query(StudentVerification)
            .filter(
                StudentVerification.user_id == user_id,
                StudentVerification.status.in_(["pending", "approved"])
            )
            .first()
        )

    def get_by_university_email(self, email: str) -> StudentVerification | None:
        return (
            self.db.query(StudentVerification)
            .filter(
                StudentVerification.university_email == email,
                StudentVerification.status.in_(["pending", "approved"])
            )
            .first()
        )

    def get_queue(self, status: str | None = None, skip: int = 0, limit: int = 100) -> list[StudentVerification]:
        query = self.db.query(StudentVerification)
        if status:
            query = query.filter(StudentVerification.status == status)
        return query.order_by(StudentVerification.created_at.desc()).offset(skip).limit(limit).all()

    def update(self, verification: StudentVerification) -> StudentVerification:
        self.db.commit()
        self.db.refresh(verification)
        return verification

    def create_history(self, history: VerificationHistory) -> VerificationHistory:
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_history_by_user_id(self, user_id: str) -> list[VerificationHistory]:
        return (
            self.db.query(VerificationHistory)
            .filter(VerificationHistory.user_id == user_id)
            .order_by(VerificationHistory.timestamp.desc())
            .all()
        )

    def get_history_by_verification_id(self, verification_id: str) -> list[VerificationHistory]:
        return (
            self.db.query(VerificationHistory)
            .filter(VerificationHistory.verification_id == verification_id)
            .order_by(VerificationHistory.timestamp.desc())
            .all()
        )
