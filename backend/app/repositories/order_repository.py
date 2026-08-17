from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem, PaymentRecord


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, order: Order) -> Order:
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def get_by_id(self, order_id: str) -> Order | None:
        return self.db.query(Order).filter(Order.id == order_id).first()

    def get_by_payment_reference(self, ref: str) -> Order | None:
        return (
            self.db.query(Order)
            .filter(Order.payment_reference == ref)
            .first()
        )

    def get_initiated_order(self, buyer_id: str, listing_id: str) -> Order | None:
        return (
            self.db.query(Order)
            .filter(
                Order.buyer_id == buyer_id,
                Order.listing_id == listing_id,
                Order.status == "initiated",
            )
            .first()
        )

    def get_by_buyer(
        self, buyer_id: str, skip: int = 0, limit: int = 20
    ) -> list[Order]:
        return (
            self.db.query(Order)
            .filter(Order.buyer_id == buyer_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_seller(
        self, seller_id: str, skip: int = 0, limit: int = 20
    ) -> list[Order]:
        return (
            self.db.query(Order)
            .filter(Order.seller_id == seller_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_seller(self, seller_id: str, status: str = "completed") -> int:
        return (
            self.db.query(func.count(Order.id))
            .filter(Order.seller_id == seller_id, Order.status == status)
            .scalar()
            or 0
        )

    def update(self, order: Order) -> Order:
        self.db.commit()
        self.db.refresh(order)
        return order

    def create_blip_record(self, rec: PaymentRecord) -> PaymentRecord:
        self.db.add(rec)
        self.db.commit()
        self.db.refresh(rec)
        return rec

    def get_blip_records_by_order_id(self, order_id: str) -> list[PaymentRecord]:
        return (
            self.db.query(PaymentRecord)
            .filter(PaymentRecord.order_id == order_id)
            .order_by(PaymentRecord.created_at.desc())
            .all()
        )

    def get_blip_record_by_reference(self, ref: str) -> PaymentRecord | None:
        return (
            self.db.query(PaymentRecord)
            .filter(PaymentRecord.payment_reference == ref)
            .first()
        )

    def create_item(self, item: OrderItem) -> OrderItem:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_items_by_order_id(self, order_id: str) -> list[OrderItem]:
        return (
            self.db.query(OrderItem)
            .filter(OrderItem.order_id == order_id)
            .order_by(OrderItem.created_at.asc())
            .all()
        )
