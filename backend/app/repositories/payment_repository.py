from sqlalchemy.orm import Session

from app.models.order import PaymentRecord


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, rec: PaymentRecord) -> PaymentRecord:
        self.db.add(rec)
        self.db.commit()
        self.db.refresh(rec)
        return rec

    def get_by_id(self, rec_id: str) -> PaymentRecord | None:
        return (
            self.db.query(PaymentRecord)
            .filter(PaymentRecord.id == rec_id)
            .first()
        )

    def get_by_reference(self, ref: str) -> PaymentRecord | None:
        return (
            self.db.query(PaymentRecord)
            .filter(PaymentRecord.payment_reference == ref)
            .first()
        )

    def get_by_order_id(self, order_id: str) -> list[PaymentRecord]:
        return (
            self.db.query(PaymentRecord)
            .filter(PaymentRecord.order_id == order_id)
            .order_by(PaymentRecord.created_at.desc())
            .all()
        )

    def update(self, rec: PaymentRecord) -> PaymentRecord:
        self.db.commit()
        self.db.refresh(rec)
        return rec
