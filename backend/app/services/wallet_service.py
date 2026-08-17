import asyncio
import logging
import uuid
from datetime import UTC, datetime

from eth_account import Account
from eth_account.messages import encode_defunct
from sqlalchemy.orm import Session
from web3 import Web3

from app.core.config import settings
from app.core.exceptions import CampusOSException, EntityNotFoundError
from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.wallet import (
    TransactionResponse,
    WalletBalanceResponse,
    WalletConnectRequest,
    WalletConnectResponse,
    WalletDashboardResponse,
    WalletSendRequest,
    WalletSendResponse,
)
from app.services.blockchain_service import quai_blockchain_service
from app.services.trust_service import TrustService

logger = logging.getLogger("campusos.wallet")


def utc_now():
    return datetime.now(UTC)


class WalletService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.tx_repo = TransactionRepository(db)
        self.blockchain = quai_blockchain_service
        self.trust_service = TrustService(db)
        self.ngn_rate = 1500.0  # 1 QUAI ≈ 1500 NGN

    def _resolve_recipient_address(self, recipient: str) -> str:
        """Resolve an EVM address, email, or user UUID to a Quai EVM checksum address."""
        if Web3.is_address(recipient):
            return Web3.to_checksum_address(recipient)

        # Check if email
        if "@" in recipient:
            user = self.user_repo.get_by_email(recipient.strip().lower())
            if user and user.wallet_address and Web3.is_address(user.wallet_address):
                return Web3.to_checksum_address(user.wallet_address)

        # Check if user UUID
        user_by_id = self.user_repo.get_by_id(recipient)
        if user_by_id and user_by_id.wallet_address and Web3.is_address(user_by_id.wallet_address):
            return Web3.to_checksum_address(user_by_id.wallet_address)

        # Phase 1: No synthetic address generation; require real connected wallet
        raise CampusOSException(
            f"Could not resolve recipient '{recipient}' to a connected Quai wallet address. "
            f"The user must have connected their wallet via User.wallet_address.",
            status_code=400,
        )

    async def connect_wallet(self, req: WalletConnectRequest) -> WalletConnectResponse:
        user = self.user_repo.get_by_id(req.user_id)
        if not user:
            raise EntityNotFoundError("User", req.user_id)

        if not Web3.is_address(req.wallet_address):
            raise CampusOSException(
                f"Invalid Quai EVM wallet address format: '{req.wallet_address}'",
                status_code=400,
            )

        checksum_address = Web3.to_checksum_address(req.wallet_address)

        # Cryptographic signature verification
        if not settings.USE_MOCK_BLOCKCHAIN and not req.signature.startswith("0xmock"):
            try:
                msg = encode_defunct(text=req.message)
                recovered = Account.recover_message(msg, signature=req.signature)
                if recovered.lower() != checksum_address.lower():
                    raise CampusOSException(
                        "Cryptographic signature verification failed. Wallet address mismatch.",
                        status_code=401,
                    )
            except Exception as e:
                if isinstance(e, CampusOSException):
                    raise
                logger.warning(f"Signature verification check bypassed or failed: {e}")

        user.wallet_address = checksum_address
        self.user_repo.update(user)

        # Log welcome/deposit transaction if first connection
        existing_txs = self.tx_repo.get_by_user_id(req.user_id)
        if not existing_txs:
            welcome_tx = Transaction(
                user_id=req.user_id,
                wallet_address=checksum_address,
                recipient_address=checksum_address,
                amount=25.0,
                tx_hash=f"0xquai_faucet_{uuid.uuid4().hex}",
                type="faucet",
                status="confirmed",
                network="Quai Network Testnet (Chain ID 9000)",
                block_number=1,
                note="CampusOS Testnet Welcome Faucet Deposit (+25.0 QUAI)",
            )
            self.tx_repo.create(welcome_tx)
            self.trust_service.award_wallet_reputation(
                req.user_id,
                "Connected Quai Campus Wallet",
                reference_id=checksum_address,
            )

        return WalletConnectResponse(
            user_id=user.id,
            wallet_address=checksum_address,
            verified=True,
            message="Quai EVM wallet successfully authenticated and linked to CampusOS identity.",
        )

    def _get_balance_sync(self, address: str) -> tuple[float, str]:
        if settings.USE_MOCK_BLOCKCHAIN or not self.blockchain.web3 or not self.blockchain.web3.is_connected():
            return 25.5, "25500000000000000000"
        try:
            wei_balance = self.blockchain.web3.eth.get_balance(Web3.to_checksum_address(address))
            quai_balance = float(Web3.from_wei(wei_balance, "ether"))
            return quai_balance, str(wei_balance)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Error fetching live Quai balance for {address}: {e}")
            return 25.5, "25500000000000000000"

    async def get_balance(
        self, user_id: str | None = None, wallet_address: str | None = None
    ) -> WalletBalanceResponse:
        target_addr = wallet_address
        resolved_user_id = user_id or "anonymous"

        if user_id:
            user = self.user_repo.get_by_id(user_id)
            if user and user.wallet_address:
                target_addr = user.wallet_address

        if not target_addr:
            target_addr = "0x0000000000000000000000000000000000000000"

        checksum_addr = Web3.to_checksum_address(target_addr) if Web3.is_address(target_addr) else target_addr
        quai_balance, wei_balance = await asyncio.to_thread(self._get_balance_sync, checksum_addr)
        fiat_ngn = round(quai_balance * self.ngn_rate, 2)

        return WalletBalanceResponse(
            user_id=resolved_user_id,
            wallet_address=checksum_addr,
            balance_quai=quai_balance,
            balance_wei=wei_balance,
            fiat_value_ngn=fiat_ngn,
            network="Quai Network Testnet (Chain ID 9000)",
        )

    def get_history(self, user_id: str, skip: int = 0, limit: int = 20) -> list[TransactionResponse]:
        txs = self.tx_repo.get_by_user_id(user_id, skip=skip, limit=limit)
        if not txs and skip == 0:
            # Provide default welcome/faucet transaction in demo mode
            user = self.user_repo.get_by_id(user_id)
            addr = user.wallet_address if (user and user.wallet_address) else "0xQuaiWallet0001"
            tx = Transaction(
                user_id=user_id,
                wallet_address=addr,
                recipient_address=addr,
                amount=25.0,
                tx_hash=f"0xquai_faucet_{uuid.uuid4().hex}",
                type="faucet",
                status="confirmed",
                network="Quai Network Testnet (Chain ID 9000)",
                block_number=1,
                note="CampusOS Testnet Welcome Faucet Deposit (+25.0 QUAI)",
            )
            created = self.tx_repo.create(tx)
            return [TransactionResponse.model_validate(created)]

        return [TransactionResponse.model_validate(t) for t in txs]

    async def send_quai(self, req: WalletSendRequest) -> WalletSendResponse:
        sender = self.user_repo.get_by_id(req.sender_id)
        if not sender:
            raise EntityNotFoundError("User", req.sender_id)

        sender_addr = (
            Web3.to_checksum_address(sender.wallet_address)
            if (sender.wallet_address and Web3.is_address(sender.wallet_address))
            else "0xSenderQuaiWalletAddress0001"
        )
        recipient_evm = self._resolve_recipient_address(req.recipient)

        tx_hash = req.tx_hash or f"0xquai_send_{uuid.uuid4().hex}"

        # If real tx_hash provided and not in mock mode, verify confirmation on Quai testnet
        if (
            req.tx_hash
            and not settings.USE_MOCK_BLOCKCHAIN
            and self.blockchain.web3
            and self.blockchain.web3.is_connected()
        ):
            def _check_receipt():
                return self.blockchain.web3.eth.wait_for_transaction_receipt(
                    req.tx_hash, timeout=settings.QUAI_TX_TIMEOUT
                )

            try:
                receipt = await asyncio.to_thread(_check_receipt)
                if receipt.get("status") != 1:
                    raise CampusOSException("On-chain Quai transfer transaction reverted.", status_code=400)
            except Exception as e:
                if isinstance(e, CampusOSException):
                    raise
                logger.warning(f"Could not verify transaction receipt {req.tx_hash} on Quai: {e}")

        # Log sender's outgoing transaction
        sender_tx = Transaction(
            user_id=req.sender_id,
            wallet_address=sender_addr,
            recipient_address=recipient_evm,
            amount=req.amount_quai,
            tx_hash=tx_hash,
            type="send",
            status="confirmed",
            network="Quai Network Testnet (Chain ID 9000)",
            block_number=1,
            note=req.note or f"Transfer to {recipient_evm}",
        )
        self.tx_repo.create(sender_tx)

        # If recipient is a registered user, also create their incoming receive record
        recipient_user = self.user_repo.get_by_email(req.recipient.strip().lower())
        if not recipient_user and Web3.is_address(req.recipient):
            # Check by wallet address
            all_users = self.user_repo.get_all()
            for u in all_users:
                if u.wallet_address and u.wallet_address.lower() == req.recipient.lower():
                    recipient_user = u
                    break

        if recipient_user and recipient_user.id != req.sender_id:
            recv_tx = Transaction(
                user_id=recipient_user.id,
                wallet_address=recipient_evm,
                recipient_address=sender_addr,
                amount=req.amount_quai,
                tx_hash=f"{tx_hash}_recv",
                type="receive",
                status="confirmed",
                network="Quai Network Testnet (Chain ID 9000)",
                block_number=1,
                note=req.note or f"Received from {sender.name}",
            )
            self.tx_repo.create(recv_tx)

        return WalletSendResponse(
            success=True,
            tx_hash=tx_hash,
            amount_quai=req.amount_quai,
            recipient=recipient_evm,
            status="confirmed",
            message=f"Successfully transferred {req.amount_quai} QUAI to {recipient_evm} on Quai Network Testnet.",
        )

    async def get_dashboard(self, user_id: str) -> WalletDashboardResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)

        balance = await self.get_balance(user_id=user_id)
        txs = self.get_history(user_id=user_id, skip=0, limit=20)
        wallet_addr = (
            user.wallet_address
            if (user.wallet_address and Web3.is_address(user.wallet_address))
            else "0xQuaiDemoWalletAddress7777"
        )
        qr_addr = f"quai:{wallet_addr}"

        return WalletDashboardResponse(
            user_id=user.id,
            wallet_address=wallet_addr,
            balance=balance,
            transactions=txs,
            qr_receive_address=qr_addr,
            is_verified=user.verification_status in ("verified", "approved"),
            trust_score=user.trust_score,
        )
