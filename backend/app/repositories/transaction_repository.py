from sqlalchemy.orm import Session

from app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, tx: Transaction) -> Transaction:
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def get_by_id(self, tx_id: str) -> Transaction | None:
        return (
            self.db.query(Transaction)
            .filter(Transaction.id == tx_id)
            .first()
        )

    def get_by_user_id(
        self, user_id: str, skip: int = 0, limit: int = 20
    ) -> list[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_wallet_address(
        self, wallet_address: str, skip: int = 0, limit: int = 20
    ) -> list[Transaction]:
        clean_addr = wallet_address.lower().strip()
        return (
            self.db.query(Transaction)
            .filter(
                (Transaction.wallet_address.ilike(f"%{clean_addr}%"))
                | (Transaction.recipient_address.ilike(f"%{clean_addr}%"))
            )
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_tx_hash(self, tx_hash: str) -> Transaction | None:
        return (
            self.db.query(Transaction)
            .filter(Transaction.tx_hash == tx_hash)
            .first()
        )
