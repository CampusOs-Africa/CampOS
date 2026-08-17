from sqlalchemy.orm import Session

from app.models.escrow import EscrowRecord


class EscrowRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, escrow: EscrowRecord) -> EscrowRecord:
        self.db.add(escrow)
        self.db.commit()
        self.db.refresh(escrow)
        return escrow

    def get_by_id(self, escrow_id: str) -> EscrowRecord | None:
        return (
            self.db.query(EscrowRecord)
            .filter(EscrowRecord.id == escrow_id)
            .first()
        )

    def get_by_order_id(self, order_id: str) -> EscrowRecord | None:
        return (
            self.db.query(EscrowRecord)
            .filter(EscrowRecord.order_id == order_id)
            .first()
        )

    def get_by_quai_order_id(self, quai_order_id: str) -> EscrowRecord | None:
        return (
            self.db.query(EscrowRecord)
            .filter(EscrowRecord.quai_order_id == quai_order_id)
            .first()
        )

    def update(self, escrow: EscrowRecord) -> EscrowRecord:
        self.db.commit()
        self.db.refresh(escrow)
        return escrow
