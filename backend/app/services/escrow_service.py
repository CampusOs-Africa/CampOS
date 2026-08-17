import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import CampusOSException, EntityNotFoundError, ForbiddenError
from app.models.escrow import EscrowRecord
from app.repositories.escrow_repository import EscrowRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.user_repository import UserRepository
from app.schemas.escrow import (
    EscrowCreateRequest,
    EscrowRecordResponse,
)
from app.services.blockchain_service import quai_blockchain_service
from app.services.trust_score_service import TrustScoreService

logger = logging.getLogger("campusos.escrow")


def utc_now():
    return datetime.now(UTC)


class EscrowService:
    def __init__(self, db: Session):
        self.db = db
        self.escrow_repo = EscrowRepository(db)
        self.order_repo = OrderRepository(db)
        self.user_repo = UserRepository(db)
        self.blockchain = quai_blockchain_service
        self.trust_service = TrustScoreService(db)

    def create_escrow(self, req: EscrowCreateRequest) -> EscrowRecordResponse:
        order = self.order_repo.get_by_id(req.order_id)
        if not order:
            raise EntityNotFoundError("Order", req.order_id)

        existing = self.escrow_repo.get_by_order_id(req.order_id)
        if existing:
            return EscrowRecordResponse.model_validate(existing)

        # Phase 1: Get real wallet addresses for buyer and seller (canonical blockchain identity)
        buyer_user = self.user_repo.get_by_id(req.buyer_id)
        seller_user = self.user_repo.get_by_id(req.seller_id)

        if not buyer_user or not buyer_user.wallet_address:
            raise EntityNotFoundError("Buyer wallet", req.buyer_id)
        if not seller_user or not seller_user.wallet_address:
            raise EntityNotFoundError("Seller wallet", req.seller_id)

        receipt = self.blockchain.createEscrow_sync(
            order_id=req.order_id,
            buyer_wallet=buyer_user.wallet_address,
            seller_wallet=seller_user.wallet_address,
            amount_wei=int(req.amount * 10**18),
        )

        quai_order_id = (
            receipt.get("quai_order_id") or f"0xquai_escrow_{uuid.uuid4().hex[:16]}"
        )
        escrow = EscrowRecord(
            order_id=req.order_id,
            buyer_id=req.buyer_id,
            seller_id=req.seller_id,
            amount=req.amount,
            state="CREATED",
            quai_order_id=quai_order_id,
            escrow_tx_hash=receipt.get("tx_hash"),
            expires_at=utc_now() + timedelta(days=14),
        )
        created = self.escrow_repo.create(escrow)
        logger.info(
            f"EscrowRecord {created.id} created for order {req.order_id} (Quai Tx: {created.escrow_tx_hash})"
        )
        return EscrowRecordResponse.model_validate(created)

    def get_escrow(self, id_or_order_id: str) -> EscrowRecordResponse:
        escrow = self.escrow_repo.get_by_id(id_or_order_id)
        if not escrow:
            escrow = self.escrow_repo.get_by_order_id(id_or_order_id)
        if not escrow:
            raise EntityNotFoundError("EscrowRecord", id_or_order_id)
        return EscrowRecordResponse.model_validate(escrow)

    def deposit_escrow(
        self, order_id: str, actor_id: str
    ) -> EscrowRecordResponse:
        escrow = self.escrow_repo.get_by_order_id(order_id)
        if not escrow:
            raise EntityNotFoundError("EscrowRecord for order", order_id)

        actor = self.user_repo.get_by_id(actor_id)
        if escrow.buyer_id != actor_id and (not actor or actor.role != "admin"):
            raise ForbiddenError(
                "Only the buyer or an administrator can deposit funds into escrow."
            )

        if escrow.state not in ("CREATED", "FUNDED"):
            raise CampusOSException(
                f"Cannot deposit into escrow in state '{escrow.state}'.",
                status_code=400,
            )

        receipt = self.blockchain.deposit_sync(order_id, int(escrow.amount * 10**18))
        escrow.state = "FUNDED"
        escrow.escrow_tx_hash = (
            receipt.get("tx_hash") or f"0xquai_escrow_deposit_{uuid.uuid4().hex[:16]}"
        )
        updated = self.escrow_repo.update(escrow)

        order = self.order_repo.get_by_id(order_id)
        if order and order.status in ("initiated", "escrow_locked"):
            order.status = "escrow_funded"
            self.order_repo.update(order)

        logger.info(
            f"EscrowRecord {updated.id} funded for order {order_id} (Tx: {updated.escrow_tx_hash})"
        )
        return EscrowRecordResponse.model_validate(updated)

    def release_escrow(
        self, order_id: str, actor_id: str
    ) -> EscrowRecordResponse:
        escrow = self.escrow_repo.get_by_order_id(order_id)
        if not escrow:
            raise EntityNotFoundError("EscrowRecord for order", order_id)

        actor = self.user_repo.get_by_id(actor_id)
        if escrow.buyer_id != actor_id and (not actor or actor.role != "admin"):
            raise ForbiddenError(
                "Only the buyer or an administrator can release escrow funds."
            )

        if escrow.state not in ("CREATED", "FUNDED", "DISPUTED"):
            raise CampusOSException(
                f"Cannot release escrow in state '{escrow.state}'.",
                status_code=400,
            )

        receipt = self.blockchain.release_sync(order_id)
        escrow.state = "COMPLETED"
        escrow.escrow_tx_hash = (
            receipt.get("tx_hash") or f"0xquai_escrow_release_{uuid.uuid4().hex[:16]}"
        )
        updated = self.escrow_repo.update(escrow)
        logger.info(
            f"EscrowRecord {updated.id} released for order {order_id} (Tx: {updated.escrow_tx_hash})"
        )
        return EscrowRecordResponse.model_validate(updated)

    def refund_escrow(
        self, order_id: str, actor_id: str, reason: str | None = None
    ) -> EscrowRecordResponse:
        escrow = self.escrow_repo.get_by_order_id(order_id)
        if not escrow:
            raise EntityNotFoundError("EscrowRecord for order", order_id)

        actor = self.user_repo.get_by_id(actor_id)
        if escrow.seller_id != actor_id and (not actor or actor.role != "admin"):
            raise ForbiddenError(
                "Only the seller or an administrator can refund escrow funds."
            )

        if escrow.state not in ("CREATED", "FUNDED", "DISPUTED"):
            raise CampusOSException(
                f"Cannot refund escrow in state '{escrow.state}'.",
                status_code=400,
            )

        receipt = self.blockchain.refund_sync(order_id)
        escrow.state = "REFUNDED"
        escrow.escrow_tx_hash = (
            receipt.get("tx_hash") or f"0xquai_escrow_refund_{uuid.uuid4().hex[:16]}"
        )
        updated = self.escrow_repo.update(escrow)
        logger.info(
            f"EscrowRecord {updated.id} refunded for order {order_id} (Reason: {reason}, Tx: {updated.escrow_tx_hash})"
        )
        return EscrowRecordResponse.model_validate(updated)

    def cancel_escrow(
        self, order_id: str, actor_id: str
    ) -> EscrowRecordResponse:
        escrow = self.escrow_repo.get_by_order_id(order_id)
        if not escrow:
            raise EntityNotFoundError("EscrowRecord for order", order_id)

        if actor_id not in (escrow.buyer_id, escrow.seller_id):
            raise ForbiddenError("Only order participants can cancel an escrow.")

        receipt = self.blockchain.cancel_sync(order_id)
        escrow.state = "CANCELLED"
        escrow.escrow_tx_hash = receipt.get("tx_hash")
        updated = self.escrow_repo.update(escrow)
        return EscrowRecordResponse.model_validate(updated)

    def dispute_escrow(
        self, order_id: str, actor_id: str, reason: str | None = None
    ) -> EscrowRecordResponse:
        escrow = self.escrow_repo.get_by_order_id(order_id)
        if not escrow:
            raise EntityNotFoundError("EscrowRecord for order", order_id)

        if actor_id not in (escrow.buyer_id, escrow.seller_id):
            raise ForbiddenError(
                "Only participants of this escrow can open a dispute."
            )

        receipt = self.blockchain.dispute_sync(order_id)
        escrow.state = "DISPUTED"
        escrow.escrow_tx_hash = receipt.get("tx_hash")
        updated = self.escrow_repo.update(escrow)
        logger.warning(
            f"EscrowRecord {updated.id} disputed for order {order_id} by {actor_id}: {reason}"
        )
        return EscrowRecordResponse.model_validate(updated)

    def resolve_dispute(
        self, order_id: str, admin_id: str, favor_seller: bool
    ) -> EscrowRecordResponse:
        escrow = self.escrow_repo.get_by_order_id(order_id)
        if not escrow:
            raise EntityNotFoundError("EscrowRecord for order", order_id)

        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.role != "admin":
            raise ForbiddenError("Only an administrator can resolve a dispute.")

        receipt = self.blockchain.resolveDispute_sync(order_id, favor_seller)
        escrow.state = "COMPLETED" if favor_seller else "REFUNDED"
        escrow.escrow_tx_hash = receipt.get("tx_hash")
        updated = self.escrow_repo.update(escrow)

        losing_party_id = escrow.buyer_id if favor_seller else escrow.seller_id
        self.trust_service.penalize_dispute_lost(
            losing_party_id, order_id=order_id, penalty=-10
        )

        logger.info(
            f"Dispute resolved for order {order_id} (favor_seller={favor_seller}, Tx: {updated.escrow_tx_hash})"
        )
        return EscrowRecordResponse.model_validate(updated)

    def refund_after_timeout(
        self, order_id: str, buyer_id: str
    ) -> EscrowRecordResponse:
        escrow = self.escrow_repo.get_by_order_id(order_id)
        if not escrow:
            raise EntityNotFoundError("EscrowRecord for order", order_id)

        if escrow.buyer_id != buyer_id:
            raise ForbiddenError("Only the buyer can claim a timeout refund.")

        receipt = self.blockchain.refundAfterTimeout_sync(order_id)
        escrow.state = "REFUNDED"
        escrow.escrow_tx_hash = receipt.get("tx_hash")
        updated = self.escrow_repo.update(escrow)
        logger.info(
            f"Timeout refund claimed for order {order_id} by buyer {buyer_id} (Tx: {updated.escrow_tx_hash})"
        )
        return EscrowRecordResponse.model_validate(updated)
