import asyncio
import hashlib
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from web3 import Web3
from web3.exceptions import Web3Exception

from app.core.config import settings
from app.core.exceptions import CampusOSException

logger = logging.getLogger("campusos.blockchain")
logging.basicConfig(level=logging.INFO)


def utc_now_iso():
    return datetime.now(UTC).isoformat()


class BlockchainService(ABC):
    @abstractmethod
    def createCredentialHash(
        self,
        user_id: str,
        email: str,
        student_id_url: str,
        admission_letter_url: str,
    ) -> str:
        """Create SHA-256 cryptographic hash of verified student identity credentials."""

    @abstractmethod
    async def registerStudent(self, user_id: str, cred_hash: str) -> dict[str, Any]:
        """Register student SHA-256 hash asynchronously on Quai Network smart contract."""

    @abstractmethod
    async def verifyStudent(self, user_id: str) -> dict[str, Any]:
        """Re-verify student on-chain asynchronously on Quai Network."""

    @abstractmethod
    async def revokeStudent(self, user_id: str) -> dict[str, Any]:
        """Revoke student on-chain asynchronously on Quai Network."""

    @abstractmethod
    async def isVerified(self, user_id: str) -> bool:
        """Check if user is verified on-chain asynchronously."""

    @abstractmethod
    async def getCredentialHash(self, user_id: str) -> str | None:
        """Get stored SHA-256 hash on-chain asynchronously."""

    @abstractmethod
    async def createEscrow(
        self, order_id: str, buyer: str, seller: str, amount_wei: int
    ) -> dict[str, Any]:
        """Create a new marketplace escrow on Quai Network MarketplaceEscrow.sol."""

    @abstractmethod
    async def deposit(self, order_id: str, amount_wei: int) -> dict[str, Any]:
        """Deposit funds into a created escrow on Quai Network."""

    @abstractmethod
    async def release(self, order_id: str) -> dict[str, Any]:
        """Release escrowed funds to seller after delivery confirmation."""

    @abstractmethod
    async def refund(self, order_id: str) -> dict[str, Any]:
        """Refund escrowed funds to buyer on Quai Network."""

    @abstractmethod
    async def cancel(self, order_id: str) -> dict[str, Any]:
        """Cancel an unfunded escrow on Quai Network."""

    @abstractmethod
    async def dispute(self, order_id: str) -> dict[str, Any]:
        """Dispute a funded escrow on Quai Network."""

    @abstractmethod
    async def resolveDispute(
        self, order_id: str, favor_seller: bool
    ) -> dict[str, Any]:
        """Resolve a disputed escrow administratively on Quai Network."""

    @abstractmethod
    async def refundAfterTimeout(self, order_id: str) -> dict[str, Any]:
        """Claim a refund after escrow timeout duration has expired."""

    # Backwards compatibility aliases (Phase 1: now accept wallet_address)
    async def storeCredentialHash(
        self, wallet_address: str, cred_hash: str
    ) -> dict[str, Any]:
        return await self.registerStudent(wallet_address, cred_hash)

    async def verifyCredential(self, wallet_address: str) -> dict[str, Any]:
        is_verif = await self.isVerified(wallet_address)
        cred_hash = await self.getCredentialHash(wallet_address)
        return {
            "wallet_address": wallet_address,
            "is_verified": is_verif,
            "credential_hash": cred_hash,
            "status": "verified" if is_verif else "unverified",
            "tx_hash": "on-chain-query",
            "timestamp": utc_now_iso(),
        }

    async def revokeCredential(self, wallet_address: str) -> dict[str, Any]:
        return await self.revokeStudent(wallet_address)


class MockBlockchainService(BlockchainService):
    """
    Mock Quai Network Blockchain Implementation.
    Simulates interaction with StudentIdentity.sol and MarketplaceEscrow.sol for local/test offline execution.
    Supports both synchronous (_sync) and asynchronous calls.
    """

    def __init__(self):
        self._storage: dict[str, str] = {}
        self._status: dict[str, str] = {}
        self._txs: dict[str, str] = {}
        self._escrows: dict[str, dict[str, Any]] = {}

    def createCredentialHash(
        self,
        user_id: str,
        email: str,
        student_id_url: str,
        admission_letter_url: str,
    ) -> str:
        payload = (
            f"{user_id}|{email.lower().strip()}|{student_id_url}|{admission_letter_url}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def registerStudent_sync(self, user_id: str, cred_hash: str) -> dict[str, Any]:
        tx_hash = f"0xquai_{uuid.uuid4().hex}"
        self._storage[user_id] = cred_hash
        self._status[user_id] = "verified"
        self._txs[user_id] = tx_hash
        logger.info(
            f"[MOCK-BLOCKCHAIN] Registered student {user_id} on-chain, cred_hash: {cred_hash}, tx_hash: {tx_hash}"
        )
        return {
            "user_id": user_id,
            "credential_hash": cred_hash,
            "tx_hash": tx_hash,
            "block_number": 1,
            "status": "verified",
            "timestamp": utc_now_iso(),
        }

    async def registerStudent(self, user_id: str, cred_hash: str) -> dict[str, Any]:
        return self.registerStudent_sync(user_id, cred_hash)

    def verifyStudent_sync(self, user_id: str) -> dict[str, Any]:
        tx_hash = f"0xquai_verif_{uuid.uuid4().hex}"
        self._status[user_id] = "verified"
        self._txs[user_id] = tx_hash
        logger.info(
            f"[MOCK-BLOCKCHAIN] Verified student {user_id} on-chain, tx_hash: {tx_hash}"
        )
        return {
            "user_id": user_id,
            "tx_hash": tx_hash,
            "block_number": 1,
            "status": "verified",
            "timestamp": utc_now_iso(),
        }

    async def verifyStudent(self, user_id: str) -> dict[str, Any]:
        return self.verifyStudent_sync(user_id)

    def revokeStudent_sync(self, user_id: str) -> dict[str, Any]:
        tx_hash = f"0xquai_revoke_{uuid.uuid4().hex}"
        self._status[user_id] = "revoked"
        self._txs[user_id] = tx_hash
        logger.info(
            f"[MOCK-BLOCKCHAIN] Revoked student {user_id} on-chain, tx_hash: {tx_hash}"
        )
        return {
            "user_id": user_id,
            "status": "revoked",
            "tx_hash": tx_hash,
            "block_number": 1,
            "timestamp": utc_now_iso(),
        }

    async def revokeStudent(self, user_id: str) -> dict[str, Any]:
        return self.revokeStudent_sync(user_id)

    async def isVerified(self, user_id: str) -> bool:
        return self._status.get(user_id) == "verified"

    async def getCredentialHash(self, user_id: str) -> str | None:
        return self._storage.get(user_id)

    # MarketplaceEscrow Mock Implementation (_sync & async)
    def createEscrow_sync(
        self, order_id: str, buyer: str, seller: str, amount_wei: int
    ) -> dict[str, Any]:
        tx_hash = f"0xquai_escrow_create_{uuid.uuid4().hex[:16]}"

        self._escrows[order_id] = {
            "order_id": order_id,
            "buyer": buyer,
            "seller": seller,
            "amount_wei": amount_wei,
            "state": "CREATED",
            "tx_hash": tx_hash,
        }

        logger.info(
            f"[MOCK-BLOCKCHAIN] Created escrow for order {order_id}, "
            f"buyer={buyer}, seller={seller}, tx_hash={tx_hash}"
        )

        return {
            "order_id": order_id,
            "tx_hash": tx_hash,
            "block_number": 1,
            "state": "CREATED",
            "event_data": {
                "event": "EscrowCreated",
                "orderId": order_id,
                "buyer": buyer,
                "seller": seller,
                "amount": amount_wei,
            },
            "timestamp": utc_now_iso(),
        }


    async def createEscrow(
        self, order_id: str, buyer: str, seller: str, amount_wei: int
    ) -> dict[str, Any]:
        return self.createEscrow_sync(order_id, buyer, seller, amount_wei)

    def deposit_sync(self, order_id: str, amount_wei: int) -> dict[str, Any]:
        tx_hash = f"0xquai_escrow_deposit_{uuid.uuid4().hex[:16]}"
        if order_id in self._escrows:
            self._escrows[order_id]["state"] = "FUNDED"
            self._escrows[order_id]["tx_hash"] = tx_hash
        logger.info(
            f"[MOCK-BLOCKCHAIN] Deposited {amount_wei} wei for escrow {order_id}, tx_hash: {tx_hash}"
        )
        return {
            "order_id": order_id,
            "tx_hash": tx_hash,
            "block_number": 2,
            "state": "FUNDED",
            "event_data": {"event": "EscrowFunded", "amount": amount_wei},
            "timestamp": utc_now_iso(),
        }

    async def deposit(self, order_id: str, amount_wei: int) -> dict[str, Any]:
        return self.deposit_sync(order_id, amount_wei)

    def release_sync(self, order_id: str) -> dict[str, Any]:
        tx_hash = f"0xquai_escrow_release_{uuid.uuid4().hex[:16]}"
        if order_id in self._escrows:
            self._escrows[order_id]["state"] = "COMPLETED"
            self._escrows[order_id]["tx_hash"] = tx_hash
        logger.info(
            f"[MOCK-BLOCKCHAIN] Released escrow {order_id} to seller, tx_hash: {tx_hash}"
        )
        return {
            "order_id": order_id,
            "tx_hash": tx_hash,
            "block_number": 3,
            "state": "COMPLETED",
            "event_data": {"event": "EscrowReleased", "orderId": order_id},
            "timestamp": utc_now_iso(),
        }

    async def release(self, order_id: str) -> dict[str, Any]:
        return self.release_sync(order_id)

    def refund_sync(self, order_id: str) -> dict[str, Any]:
        tx_hash = f"0xquai_escrow_refund_{uuid.uuid4().hex[:16]}"
        if order_id in self._escrows:
            self._escrows[order_id]["state"] = "REFUNDED"
            self._escrows[order_id]["tx_hash"] = tx_hash
        logger.info(
            f"[MOCK-BLOCKCHAIN] Refunded escrow {order_id} to buyer, tx_hash: {tx_hash}"
        )
        return {
            "order_id": order_id,
            "tx_hash": tx_hash,
            "block_number": 4,
            "state": "REFUNDED",
            "event_data": {"event": "EscrowRefunded", "orderId": order_id},
            "timestamp": utc_now_iso(),
        }

    async def refund(self, order_id: str) -> dict[str, Any]:
        return self.refund_sync(order_id)

    def cancel_sync(self, order_id: str) -> dict[str, Any]:
        tx_hash = f"0xquai_escrow_cancel_{uuid.uuid4().hex[:16]}"
        if order_id in self._escrows:
            self._escrows[order_id]["state"] = "CANCELLED"
            self._escrows[order_id]["tx_hash"] = tx_hash
        logger.info(
            f"[MOCK-BLOCKCHAIN] Cancelled escrow {order_id}, tx_hash: {tx_hash}"
        )
        return {
            "order_id": order_id,
            "tx_hash": tx_hash,
            "block_number": 5,
            "state": "CANCELLED",
            "event_data": {"event": "EscrowCancelled", "orderId": order_id},
            "timestamp": utc_now_iso(),
        }

    async def cancel(self, order_id: str) -> dict[str, Any]:
        return self.cancel_sync(order_id)

    def dispute_sync(self, order_id: str) -> dict[str, Any]:
        tx_hash = f"0xquai_escrow_dispute_{uuid.uuid4().hex[:16]}"
        if order_id in self._escrows:
            self._escrows[order_id]["state"] = "DISPUTED"
            self._escrows[order_id]["tx_hash"] = tx_hash
        logger.info(
            f"[MOCK-BLOCKCHAIN] Disputed escrow {order_id}, tx_hash: {tx_hash}"
        )
        return {
            "order_id": order_id,
            "tx_hash": tx_hash,
            "block_number": 6,
            "state": "DISPUTED",
            "event_data": {"event": "EscrowDisputed", "orderId": order_id},
            "timestamp": utc_now_iso(),
        }

    async def dispute(self, order_id: str) -> dict[str, Any]:
        return self.dispute_sync(order_id)

    def resolveDispute_sync(
        self, order_id: str, favor_seller: bool
    ) -> dict[str, Any]:
        tx_hash = f"0xquai_escrow_resolve_{uuid.uuid4().hex[:16]}"
        new_state = "COMPLETED" if favor_seller else "REFUNDED"
        if order_id in self._escrows:
            self._escrows[order_id]["state"] = new_state
            self._escrows[order_id]["tx_hash"] = tx_hash
        logger.info(
            f"[MOCK-BLOCKCHAIN] Resolved dispute for {order_id} (favor_seller={favor_seller}), tx_hash: {tx_hash}"
        )
        return {
            "order_id": order_id,
            "tx_hash": tx_hash,
            "block_number": 7,
            "state": new_state,
            "event_data": {
                "event": "DisputeResolved",
                "favorSeller": favor_seller,
            },
            "timestamp": utc_now_iso(),
        }

    async def resolveDispute(
        self, order_id: str, favor_seller: bool
    ) -> dict[str, Any]:
        return self.resolveDispute_sync(order_id, favor_seller)

    def refundAfterTimeout_sync(self, order_id: str) -> dict[str, Any]:
        tx_hash = f"0xquai_escrow_timeout_{uuid.uuid4().hex[:16]}"
        if order_id in self._escrows:
            self._escrows[order_id]["state"] = "REFUNDED"
            self._escrows[order_id]["tx_hash"] = tx_hash
        logger.info(
            f"[MOCK-BLOCKCHAIN] Timeout refund for {order_id}, tx_hash: {tx_hash}"
        )
        return {
            "order_id": order_id,
            "tx_hash": tx_hash,
            "block_number": 8,
            "state": "REFUNDED",
            "event_data": {"event": "EscrowRefunded", "orderId": order_id},
            "timestamp": utc_now_iso(),
        }

    async def refundAfterTimeout(self, order_id: str) -> dict[str, Any]:
        return self.refundAfterTimeout_sync(order_id)


_onchain_verification_cache: dict[str, tuple[bool, float]] = {}


class QuaiBlockchainService(BlockchainService):
    """
    Production Quai Network Blockchain Implementation for Milestone 3 & 5.
    Interacts with deployed StudentIdentity.sol and MarketplaceEscrow.sol contracts on Quai EVM Testnet.
    """

    def __init__(self):
        self.mock = MockBlockchainService()
        self.web3: Web3 | None = None
        self.identity_contract: Any | None = None
        self.escrow_contract: Any | None = None
        self.account: Any | None = None
        self.identity_abi: list[dict[str, Any]] | None = None
        self.escrow_abi: list[dict[str, Any]] | None = None

        self._storage_fallback: dict[str, str] = {}
        self._status_fallback: dict[str, str] = {}
        self._txs_fallback: dict[str, str] = {}

        if not settings.USE_MOCK_BLOCKCHAIN:
            self._initialize_web3()

    def _load_contract_abi(self, contract_name: str) -> list[dict[str, Any]] | None:
        """Read ABI from contracts/artifacts first, then fallback paths."""
        possible_paths = [
            Path(__file__).parent.parent.parent.parent
            / "contracts"
            / "artifacts"
            / "contracts"
            / f"{contract_name}.sol"
            / f"{contract_name}.json",
            Path(__file__).parent.parent.parent.parent
            / "contracts"
            / "abi"
            / f"{contract_name}.json",
            Path(__file__).parent.parent
            / "contracts"
            / f"{contract_name.lower()}_abi.json",
        ]
        for p in possible_paths:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    abi = data.get("abi", data) if isinstance(data, dict) else data
                    logger.info(f"Loaded {contract_name} contract ABI from {p}")
                    return abi
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Error reading ABI from {p}: {e}")
        return None

    def _initialize_web3(self) -> None:
        try:
            self.web3 = Web3(
                Web3.HTTPProvider(
                    settings.QUAI_RPC_URL,
                    request_kwargs={"timeout": settings.QUAI_RPC_TIMEOUT},
                )
            )
            if self.web3.is_connected():
                logger.info(
                    f"Connected to Quai Network RPC at {settings.QUAI_RPC_URL} (Chain ID: {settings.QUAI_CHAIN_ID})"
                )
                self.account = self.web3.eth.account.from_key(
                    settings.QUAI_PRIVATE_KEY
                )
                self.identity_abi = self._load_contract_abi("StudentIdentity")
                self.escrow_abi = self._load_contract_abi("MarketplaceEscrow")

                if self.identity_abi:
                    self.identity_contract = self.web3.eth.contract(
                        address=Web3.to_checksum_address(
                            settings.QUAI_CONTRACT_ADDRESS
                        ),
                        abi=self.identity_abi,
                    )
                    logger.info(
                        f"StudentIdentity smart contract initialized at {settings.QUAI_CONTRACT_ADDRESS}"
                    )
                if self.escrow_abi:
                    self.escrow_contract = self.web3.eth.contract(
                        address=Web3.to_checksum_address(
                            settings.QUAI_ESCROW_CONTRACT_ADDRESS
                        ),
                        abi=self.escrow_abi,
                    )
                    logger.info(
                        f"MarketplaceEscrow smart contract initialized at {settings.QUAI_ESCROW_CONTRACT_ADDRESS}"
                    )
            else:
                logger.warning(
                    f"Could not connect to Quai Network RPC at {settings.QUAI_RPC_URL}"
                )
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error initializing QuaiBlockchainService: {e}")

    def _resolve_evm_address(self, wallet_address: str) -> str:
        """Resolve a real EVM address or deterministically derive one from a UUID."""
        if Web3.is_address(wallet_address):
            return Web3.to_checksum_address(wallet_address)

        try:
            uuid.UUID(wallet_address)
        except (ValueError, AttributeError):
            raise CampusOSException(
                f"Invalid EVM address or user UUID: '{wallet_address}'.",
                status_code=400,
            )

        # Deterministically derive a valid 20-byte EVM address from the UUID.
        address_bytes = hashlib.sha256(wallet_address.encode("utf-8")).digest()[-20:]
        derived_address = Web3.to_checksum_address(Web3.to_hex(address_bytes))

        return derived_address

    def _resolve_order_id_bytes32(self, order_id: str) -> bytes:
        """Resolve an order UUID or hex string to a deterministic 32-byte Quai bytes32 identifier."""
        if order_id.startswith("0x") and len(order_id) <= 66:
            return bytes.fromhex(order_id[2:].ljust(64, "0")[:64])
        return hashlib.sha256(order_id.encode("utf-8")).digest()

    def _execute_with_retry_sync(
        self, fn: Any, *args: Any, max_retries: int = 3, base_delay: float = 1.0
    ) -> Any:
        """Execute synchronous RPC call or transaction with exponential backoff retry logic."""
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                return fn(*args)
            except (OSError, Web3Exception, Exception) as e:  # noqa: BLE001
                last_exception = e
                logger.warning(
                    f"Quai Network RPC attempt {attempt}/{max_retries} failed: {e}. Retrying in {base_delay}s..."
                )
                time.sleep(base_delay)
                base_delay *= 2.0
        logger.error(
            f"Quai Network operation failed after {max_retries} attempts: {last_exception}"
        )
        raise CampusOSException(f"Quai Network RPC failure: {last_exception}")

    def _parse_tx_receipt(
        self,
        receipt: dict[str, Any],
        event_name: str | None = None,
        contract: Any | None = None,
    ) -> dict[str, Any]:
        """Parse Quai Network transaction receipt, verify status, and decode emitted events."""
        status = receipt.get("status", 1)
        if status != 1:
            raise CampusOSException("Quai Network transaction reverted on-chain.")

        tx_hash_hex = (
            receipt["transactionHash"].hex()
            if hasattr(receipt["transactionHash"], "hex")
            else str(receipt["transactionHash"])
        )
        block_num = receipt.get("blockNumber", 1)
        gas_used = receipt.get("gasUsed", 0)

        event_data = {}
        if event_name and contract:
            try:
                logs = contract.events[event_name]().process_receipt(receipt)
                if logs and len(logs) > 0:
                    event_data = dict(logs[0].get("args", {}))
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    f"Could not decode event '{event_name}' from receipt {tx_hash_hex}: {e}"
                )

        return {
            "tx_hash": tx_hash_hex,
            "block_number": block_num,
            "gas_used": gas_used,
            "event_data": event_data,
            "timestamp": utc_now_iso(),
        }

    def _estimate_gas_safe(self, tx_params: dict[str, Any], default_gas: int = 200000) -> int:
        """Estimate gas with safe default fallback."""
        if not self.web3:
            return default_gas
        try:
            return int(self.web3.eth.estimate_gas(tx_params) * 1.2)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Gas estimation failed, using fallback {default_gas}: {e}")
            return default_gas

    def createCredentialHash(
        self,
        user_id: str,
        email: str,
        student_id_url: str,
        admission_letter_url: str,
    ) -> str:
        payload = (
            f"{user_id}|{email.lower().strip()}|{student_id_url}|{admission_letter_url}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _register_student_sync(self, wallet_address: str, cred_hash: str) -> dict[str, Any]:
        evm_address_lower = wallet_address.lower()
        _onchain_verification_cache.pop(evm_address_lower, None)
        if (
            settings.USE_MOCK_BLOCKCHAIN
            or not self.identity_contract
            or not self.web3
        ):
            tx_hash = f"0xquai_{uuid.uuid4().hex}"
            self._storage_fallback[evm_address_lower] = cred_hash
            self._status_fallback[evm_address_lower] = "verified"
            self._txs_fallback[evm_address_lower] = tx_hash
            logger.info(
                f"[FALLBACK-MOCK] Registered student {evm_address_lower} on-chain, cred_hash: {cred_hash}, tx_hash: {tx_hash}"
            )
            return {
                "wallet_address": evm_address_lower,
                "credential_hash": cred_hash,
                "tx_hash": tx_hash,
                "block_number": 1,
                "status": "verified",
                "timestamp": utc_now_iso(),
            }

        evm_address = self._resolve_evm_address(wallet_address)
        cred_bytes32 = bytes.fromhex(cred_hash)
        logger.info(
            f"Initiating Quai transaction: registerStudent({evm_address}, {cred_hash[:10]}...)"
        )

        def _send_tx():
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            tx = self.identity_contract.functions.registerStudent(
                evm_address, cred_bytes32
            ).build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                "gas": 150000,
                "gasPrice": self.web3.eth.gas_price,
                "chainId": settings.QUAI_CHAIN_ID,
            })
            signed_tx = self.web3.eth.account.sign_transaction(
                tx, private_key=settings.QUAI_PRIVATE_KEY
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(
                f"Broadcasted registerStudent transaction on Quai Network: {tx_hash.hex()}"
            )
            return self.web3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=settings.QUAI_TX_TIMEOUT, poll_latency=2.0
            )

        receipt = self._execute_with_retry_sync(_send_tx)
        parsed = self._parse_tx_receipt(
            receipt, event_name="StudentRegistered", contract=self.identity_contract
        )
        logger.info(
            f"registerStudent confirmed in block {parsed['block_number']} - status: SUCCESS - tx_hash: {parsed['tx_hash']}"
        )
        return {
            "wallet_address": evm_address,
            "credential_hash": cred_hash,
            "tx_hash": parsed["tx_hash"],
            "block_number": parsed["block_number"],
            "status": "verified",
            "timestamp": utc_now_iso(),
        }

    async def registerStudent(self, wallet_address: str, cred_hash: str) -> dict[str, Any]:
        """Asynchronously register a student on Quai Network using their real wallet address."""
        return await asyncio.to_thread(self._register_student_sync, wallet_address, cred_hash)

    def _verify_student_sync(self, wallet_address: str) -> dict[str, Any]:
        evm_address_lower = wallet_address.lower()
        _onchain_verification_cache.pop(evm_address_lower, None)
        if (
            settings.USE_MOCK_BLOCKCHAIN
            or not self.identity_contract
            or not self.web3
        ):
            tx_hash = f"0xquai_verif_{uuid.uuid4().hex}"
            self._status_fallback[evm_address_lower] = "verified"
            self._txs_fallback[evm_address_lower] = tx_hash
            logger.info(
                f"[FALLBACK-MOCK] Verified student {evm_address_lower} on-chain, tx_hash: {tx_hash}"
            )
            return {
                "wallet_address": evm_address_lower,
                "tx_hash": tx_hash,
                "block_number": 1,
                "status": "verified",
                "timestamp": utc_now_iso(),
            }

        evm_address = self._resolve_evm_address(wallet_address)
        logger.info(f"Initiating Quai transaction: verifyStudent({evm_address})")

        def _send_tx():
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            tx = self.identity_contract.functions.verifyStudent(
                evm_address
            ).build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                "gas": 100000,
                "gasPrice": self.web3.eth.gas_price,
                "chainId": settings.QUAI_CHAIN_ID,
            })
            signed_tx = self.web3.eth.account.sign_transaction(
                tx, private_key=settings.QUAI_PRIVATE_KEY
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(
                f"Broadcasted verifyStudent transaction on Quai Network: {tx_hash.hex()}"
            )
            return self.web3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=settings.QUAI_TX_TIMEOUT, poll_latency=2.0
            )

        receipt = self._execute_with_retry_sync(_send_tx)
        parsed = self._parse_tx_receipt(
            receipt, event_name="StudentVerified", contract=self.identity_contract
        )
        return {
            "wallet_address": evm_address,
            "tx_hash": parsed["tx_hash"],
            "block_number": parsed["block_number"],
            "status": "verified",
            "timestamp": utc_now_iso(),
        }

    async def verifyStudent(self, wallet_address: str) -> dict[str, Any]:
        """Asynchronously verify a student on Quai Network using their real wallet address."""
        return await asyncio.to_thread(self._verify_student_sync, wallet_address)

    def _revoke_student_sync(self, wallet_address: str) -> dict[str, Any]:
        evm_address_lower = wallet_address.lower()
        _onchain_verification_cache.pop(evm_address_lower, None)
        if (
            settings.USE_MOCK_BLOCKCHAIN
            or not self.identity_contract
            or not self.web3
        ):
            tx_hash = f"0xquai_revoke_{uuid.uuid4().hex}"
            self._status_fallback[evm_address_lower] = "revoked"
            self._txs_fallback[evm_address_lower] = tx_hash
            logger.info(
                f"[FALLBACK-MOCK] Revoked student {evm_address_lower} on-chain, tx_hash: {tx_hash}"
            )
            return {
                "wallet_address": evm_address_lower,
                "status": "revoked",
                "tx_hash": tx_hash,
                "block_number": 1,
                "timestamp": utc_now_iso(),
            }
            

        evm_address = self._resolve_evm_address(wallet_address)
        logger.info(f"Initiating Quai transaction: revokeStudent({evm_address})")

        def _send_revoke_tx():
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            tx = self.identity_contract.functions.revokeStudent(
                evm_address
            ).build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                "gas": 100000,
                "gasPrice": self.web3.eth.gas_price,
                "chainId": settings.QUAI_CHAIN_ID,
            })
            signed_tx = self.web3.eth.account.sign_transaction(
                tx, private_key=settings.QUAI_PRIVATE_KEY
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(
                f"Broadcasted revokeStudent transaction on Quai Network: {tx_hash.hex()}"
            )
            return self.web3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=settings.QUAI_TX_TIMEOUT, poll_latency=2.0
            )

        receipt = self._execute_with_retry_sync(_send_revoke_tx)
        parsed = self._parse_tx_receipt(
            receipt, event_name="StudentRevoked", contract=self.identity_contract
        )
        return {
            "wallet_address": evm_address,
            "status": "revoked",
            "tx_hash": parsed["tx_hash"],
            "block_number": parsed["block_number"],
            "timestamp": utc_now_iso(),
        }

    async def revokeStudent(self, wallet_address: str) -> dict[str, Any]:
        """Asynchronously revoke a student on Quai Network using their real wallet address."""
        return await asyncio.to_thread(self._revoke_student_sync, wallet_address)

    def _is_verified_sync(self, wallet_address: str) -> bool:
        evm_address_lower = wallet_address.lower()
        now = time.time()
        cached = _onchain_verification_cache.get(evm_address_lower)
        if cached and now < cached[1]:
            return cached[0]

        if (
            settings.USE_MOCK_BLOCKCHAIN
            or not self.identity_contract
            or not self.web3
        ):
            val = (
                self._status_fallback.get(evm_address_lower) == "verified"
                or self.mock._status.get(evm_address_lower) == "verified"
            )
            _onchain_verification_cache[evm_address_lower] = (val, now + 15.0)
            return val

        evm_address = self._resolve_evm_address(wallet_address)
        val = self._execute_with_retry_sync(
            lambda: self.identity_contract.functions.isVerified(
                evm_address
            ).call()
        )
        _onchain_verification_cache[evm_address_lower] = (val, now + 15.0)
        return val

    async def isVerified(self, wallet_address: str) -> bool:
        """Asynchronously query if a student is verified on Quai Network using their real wallet address."""
        return await asyncio.to_thread(self._is_verified_sync, wallet_address)

    def _get_cred_hash_sync(self, wallet_address: str) -> str | None:
        evm_address_lower = wallet_address.lower()
        if (
            settings.USE_MOCK_BLOCKCHAIN
            or not self.identity_contract
            or not self.web3
        ):
            return self._storage_fallback.get(evm_address_lower)

        evm_address = self._resolve_evm_address(wallet_address)
        stored_bytes = self._execute_with_retry_sync(
            lambda: self.identity_contract.functions.getCredentialHash(
                evm_address
            ).call()
        )
        return stored_bytes.hex() if stored_bytes != b"\x00" * 32 else None

    async def getCredentialHash(self, wallet_address: str) -> str | None:
        """Asynchronously query the stored SHA-256 hash on Quai Network using their real wallet address."""
        return await asyncio.to_thread(self._get_cred_hash_sync, wallet_address)

    async def verifyCredential(self, wallet_address: str) -> dict[str, Any]:
        is_verif = await self.isVerified(wallet_address)
        cred_hash = await self.getCredentialHash(wallet_address)
        evm_address_lower = wallet_address.lower()
        tx_hash = self._txs_fallback.get(evm_address_lower, "on-chain-query")
        return {
            "wallet_address": evm_address_lower,
            "is_verified": is_verif,
            "credential_hash": cred_hash,
            "status": "verified" if is_verif else "unverified",
            "tx_hash": tx_hash,
            "timestamp": utc_now_iso(),
        }

    # -------------------------------------------------------------------------
    # MarketplaceEscrow Smart Contract Methods (Milestone 5)
    # -------------------------------------------------------------------------

    def _create_escrow_sync(
        self, order_id: str, buyer_wallet: str, seller_wallet: str, amount_wei: int
    ) -> dict[str, Any]:
        if settings.USE_MOCK_BLOCKCHAIN or not self.escrow_contract or not self.web3:
            return self.mock.createEscrow_sync(order_id, buyer_wallet, seller_wallet, amount_wei)

        buyer_evm = self._resolve_evm_address(buyer_wallet)
        seller_evm = self._resolve_evm_address(seller_wallet)
        order_id_bytes = self._resolve_order_id_bytes32(order_id)
        logger.info(
            f"Initiating Quai transaction: createEscrow({order_id}, {buyer_evm}, {seller_evm}, {amount_wei})"
        )

        def _send_tx():
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            tx_params = {
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": self.web3.eth.gas_price,
                "chainId": settings.QUAI_CHAIN_ID,
            }
            fn = self.escrow_contract.functions.createEscrow(
                order_id_bytes, buyer_evm, seller_evm, amount_wei
            )
            tx_params["gas"] = self._estimate_gas_safe(fn.build_transaction(tx_params), 250000)
            signed_tx = self.web3.eth.account.sign_transaction(
                fn.build_transaction(tx_params), private_key=settings.QUAI_PRIVATE_KEY
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"Broadcasted createEscrow on Quai Network: {tx_hash.hex()}")
            return self.web3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=settings.QUAI_TX_TIMEOUT, poll_latency=2.0
            )

        receipt = self._execute_with_retry_sync(_send_tx)
        parsed = self._parse_tx_receipt(
            receipt, event_name="EscrowCreated", contract=self.escrow_contract
        )
        return {
            "order_id": order_id,
            "tx_hash": parsed["tx_hash"],
            "block_number": parsed["block_number"],
            "state": "CREATED",
            "event_data": parsed["event_data"],
            "timestamp": utc_now_iso(),
        }

    async def createEscrow(
        self, order_id: str, buyer_wallet: str, seller_wallet: str, amount_wei: int
    ) -> dict[str, Any]:
        """Asynchronously create smart contract escrow on Quai Network using real wallet addresses."""
        return await asyncio.to_thread(
            self._create_escrow_sync, order_id, buyer_wallet, seller_wallet, amount_wei
        )

    def _deposit_sync(self, order_id: str, amount_wei: int) -> dict[str, Any]:
        if settings.USE_MOCK_BLOCKCHAIN or not self.escrow_contract or not self.web3:
            return self.mock.deposit_sync(order_id, amount_wei)

        order_id_bytes = self._resolve_order_id_bytes32(order_id)
        logger.info(f"Initiating Quai transaction: deposit({order_id}, {amount_wei})")

        def _send_tx():
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            tx_params = {
                "from": self.account.address,
                "value": amount_wei,
                "nonce": nonce,
                "gasPrice": self.web3.eth.gas_price,
                "chainId": settings.QUAI_CHAIN_ID,
            }
            fn = self.escrow_contract.functions.deposit(order_id_bytes)
            tx_params["gas"] = self._estimate_gas_safe(fn.build_transaction(tx_params), 150000)
            signed_tx = self.web3.eth.account.sign_transaction(
                fn.build_transaction(tx_params), private_key=settings.QUAI_PRIVATE_KEY
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"Broadcasted deposit on Quai Network: {tx_hash.hex()}")
            return self.web3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=settings.QUAI_TX_TIMEOUT, poll_latency=2.0
            )

        receipt = self._execute_with_retry_sync(_send_tx)
        parsed = self._parse_tx_receipt(
            receipt, event_name="EscrowFunded", contract=self.escrow_contract
        )
        return {
            "order_id": order_id,
            "tx_hash": parsed["tx_hash"],
            "block_number": parsed["block_number"],
            "state": "FUNDED",
            "event_data": parsed["event_data"],
            "timestamp": utc_now_iso(),
        }

    async def deposit(self, order_id: str, amount_wei: int) -> dict[str, Any]:
        """Asynchronously deposit funds into smart contract escrow on Quai Network."""
        return await asyncio.to_thread(self._deposit_sync, order_id, amount_wei)

    def _release_sync(self, order_id: str) -> dict[str, Any]:
        if settings.USE_MOCK_BLOCKCHAIN or not self.escrow_contract or not self.web3:
            return self.mock.release_sync(order_id)

        order_id_bytes = self._resolve_order_id_bytes32(order_id)
        logger.info(f"Initiating Quai transaction: release({order_id})")

        def _send_tx():
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            tx_params = {
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": self.web3.eth.gas_price,
                "chainId": settings.QUAI_CHAIN_ID,
            }
            fn = self.escrow_contract.functions.release(order_id_bytes)
            tx_params["gas"] = self._estimate_gas_safe(fn.build_transaction(tx_params), 150000)
            signed_tx = self.web3.eth.account.sign_transaction(
                fn.build_transaction(tx_params), private_key=settings.QUAI_PRIVATE_KEY
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"Broadcasted release on Quai Network: {tx_hash.hex()}")
            return self.web3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=settings.QUAI_TX_TIMEOUT, poll_latency=2.0
            )

        receipt = self._execute_with_retry_sync(_send_tx)
        parsed = self._parse_tx_receipt(
            receipt, event_name="EscrowReleased", contract=self.escrow_contract
        )
        return {
            "order_id": order_id,
            "tx_hash": parsed["tx_hash"],
            "block_number": parsed["block_number"],
            "state": "COMPLETED",
            "event_data": parsed["event_data"],
            "timestamp": utc_now_iso(),
        }

    async def release(self, order_id: str) -> dict[str, Any]:
        """Asynchronously release escrow funds on Quai Network."""
        return await asyncio.to_thread(self._release_sync, order_id)

    def _refund_sync(self, order_id: str) -> dict[str, Any]:
        if settings.USE_MOCK_BLOCKCHAIN or not self.escrow_contract or not self.web3:
            return self.mock.refund_sync(order_id)

        order_id_bytes = self._resolve_order_id_bytes32(order_id)
        logger.info(f"Initiating Quai transaction: refund({order_id})")

        def _send_tx():
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            tx_params = {
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": self.web3.eth.gas_price,
                "chainId": settings.QUAI_CHAIN_ID,
            }
            fn = self.escrow_contract.functions.refund(order_id_bytes)
            tx_params["gas"] = self._estimate_gas_safe(fn.build_transaction(tx_params), 150000)
            signed_tx = self.web3.eth.account.sign_transaction(
                fn.build_transaction(tx_params), private_key=settings.QUAI_PRIVATE_KEY
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"Broadcasted refund on Quai Network: {tx_hash.hex()}")
            return self.web3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=settings.QUAI_TX_TIMEOUT, poll_latency=2.0
            )

        receipt = self._execute_with_retry_sync(_send_tx)
        parsed = self._parse_tx_receipt(
            receipt, event_name="EscrowRefunded", contract=self.escrow_contract
        )
        return {
            "order_id": order_id,
            "tx_hash": parsed["tx_hash"],
            "block_number": parsed["block_number"],
            "state": "REFUNDED",
            "event_data": parsed["event_data"],
            "timestamp": utc_now_iso(),
        }

    async def refund(self, order_id: str) -> dict[str, Any]:
        """Asynchronously refund escrow funds on Quai Network."""
        return await asyncio.to_thread(self._refund_sync, order_id)

    def _cancel_sync(self, order_id: str) -> dict[str, Any]:
        if settings.USE_MOCK_BLOCKCHAIN or not self.escrow_contract or not self.web3:
            return self.mock.cancel_sync(order_id)

        order_id_bytes = self._resolve_order_id_bytes32(order_id)
        logger.info(f"Initiating Quai transaction: cancel({order_id})")

        def _send_tx():
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            tx_params = {
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": self.web3.eth.gas_price,
                "chainId": settings.QUAI_CHAIN_ID,
            }
            fn = self.escrow_contract.functions.cancel(order_id_bytes)
            tx_params["gas"] = self._estimate_gas_safe(fn.build_transaction(tx_params), 100000)
            signed_tx = self.web3.eth.account.sign_transaction(
                fn.build_transaction(tx_params), private_key=settings.QUAI_PRIVATE_KEY
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"Broadcasted cancel on Quai Network: {tx_hash.hex()}")
            return self.web3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=settings.QUAI_TX_TIMEOUT, poll_latency=2.0
            )

        receipt = self._execute_with_retry_sync(_send_tx)
        parsed = self._parse_tx_receipt(
            receipt, event_name="EscrowCancelled", contract=self.escrow_contract
        )
        return {
            "order_id": order_id,
            "tx_hash": parsed["tx_hash"],
            "block_number": parsed["block_number"],
            "state": "CANCELLED",
            "event_data": parsed["event_data"],
            "timestamp": utc_now_iso(),
        }

    async def cancel(self, order_id: str) -> dict[str, Any]:
        """Asynchronously cancel an unfunded escrow on Quai Network."""
        return await asyncio.to_thread(self._cancel_sync, order_id)

    def _dispute_sync(self, order_id: str) -> dict[str, Any]:
        if settings.USE_MOCK_BLOCKCHAIN or not self.escrow_contract or not self.web3:
            return self.mock.dispute_sync(order_id)

        order_id_bytes = self._resolve_order_id_bytes32(order_id)
        logger.info(f"Initiating Quai transaction: dispute({order_id})")

        def _send_tx():
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            tx_params = {
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": self.web3.eth.gas_price,
                "chainId": settings.QUAI_CHAIN_ID,
            }
            fn = self.escrow_contract.functions.dispute(order_id_bytes)
            tx_params["gas"] = self._estimate_gas_safe(fn.build_transaction(tx_params), 100000)
            signed_tx = self.web3.eth.account.sign_transaction(
                fn.build_transaction(tx_params), private_key=settings.QUAI_PRIVATE_KEY
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"Broadcasted dispute on Quai Network: {tx_hash.hex()}")
            return self.web3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=settings.QUAI_TX_TIMEOUT, poll_latency=2.0
            )

        receipt = self._execute_with_retry_sync(_send_tx)
        parsed = self._parse_tx_receipt(
            receipt, event_name="EscrowDisputed", contract=self.escrow_contract
        )
        return {
            "order_id": order_id,
            "tx_hash": parsed["tx_hash"],
            "block_number": parsed["block_number"],
            "state": "DISPUTED",
            "event_data": parsed["event_data"],
            "timestamp": utc_now_iso(),
        }

    async def dispute(self, order_id: str) -> dict[str, Any]:
        """Asynchronously dispute a funded escrow on Quai Network."""
        return await asyncio.to_thread(self._dispute_sync, order_id)

    def _resolve_dispute_sync(
        self, order_id: str, favor_seller: bool
    ) -> dict[str, Any]:
        if settings.USE_MOCK_BLOCKCHAIN or not self.escrow_contract or not self.web3:
            return self.mock.resolveDispute_sync(order_id, favor_seller)

        order_id_bytes = self._resolve_order_id_bytes32(order_id)
        logger.info(
            f"Initiating Quai transaction: resolveDispute({order_id}, favorSeller={favor_seller})"
        )

        def _send_tx():
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            tx_params = {
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": self.web3.eth.gas_price,
                "chainId": settings.QUAI_CHAIN_ID,
            }
            fn = self.escrow_contract.functions.resolveDispute(order_id_bytes, favor_seller)
            tx_params["gas"] = self._estimate_gas_safe(fn.build_transaction(tx_params), 150000)
            signed_tx = self.web3.eth.account.sign_transaction(
                fn.build_transaction(tx_params), private_key=settings.QUAI_PRIVATE_KEY
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"Broadcasted resolveDispute on Quai Network: {tx_hash.hex()}")
            return self.web3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=settings.QUAI_TX_TIMEOUT, poll_latency=2.0
            )

        receipt = self._execute_with_retry_sync(_send_tx)
        parsed = self._parse_tx_receipt(
            receipt, event_name="DisputeResolved", contract=self.escrow_contract
        )
        new_state = "COMPLETED" if favor_seller else "REFUNDED"
        return {
            "order_id": order_id,
            "tx_hash": parsed["tx_hash"],
            "block_number": parsed["block_number"],
            "state": new_state,
            "event_data": parsed["event_data"],
            "timestamp": utc_now_iso(),
        }

    async def resolveDispute(
        self, order_id: str, favor_seller: bool
    ) -> dict[str, Any]:
        """Asynchronously resolve a disputed escrow on Quai Network."""
        return await asyncio.to_thread(
            self._resolve_dispute_sync, order_id, favor_seller
        )

    def _refund_after_timeout_sync(self, order_id: str) -> dict[str, Any]:
        if settings.USE_MOCK_BLOCKCHAIN or not self.escrow_contract or not self.web3:
            return self.mock.refundAfterTimeout_sync(order_id)

        order_id_bytes = self._resolve_order_id_bytes32(order_id)
        logger.info(
            f"Initiating Quai transaction: refundAfterTimeout({order_id})"
        )

        def _send_tx():
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            tx_params = {
                "from": self.account.address,
                "nonce": nonce,
                "gasPrice": self.web3.eth.gas_price,
                "chainId": settings.QUAI_CHAIN_ID,
            }
            fn = self.escrow_contract.functions.refundAfterTimeout(order_id_bytes)
            tx_params["gas"] = self._estimate_gas_safe(fn.build_transaction(tx_params), 150000)
            signed_tx = self.web3.eth.account.sign_transaction(
                fn.build_transaction(tx_params), private_key=settings.QUAI_PRIVATE_KEY
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(
                f"Broadcasted refundAfterTimeout on Quai Network: {tx_hash.hex()}"
            )
            return self.web3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=settings.QUAI_TX_TIMEOUT, poll_latency=2.0
            )

        receipt = self._execute_with_retry_sync(_send_tx)
        parsed = self._parse_tx_receipt(
            receipt, event_name="EscrowRefunded", contract=self.escrow_contract
        )
        return {
            "order_id": order_id,
            "tx_hash": parsed["tx_hash"],
            "block_number": parsed["block_number"],
            "state": "REFUNDED",
            "event_data": parsed["event_data"],
            "timestamp": utc_now_iso(),
        }

    async def refundAfterTimeout(self, order_id: str) -> dict[str, Any]:
        """Asynchronously claim timeout refund on Quai Network."""
        return await asyncio.to_thread(self._refund_after_timeout_sync, order_id)

    # Synchronous wrappers for non-async callers in domain services
    def createEscrow_sync(
        self,
        order_id: str,
        buyer: str | None = None,
        seller: str | None = None,
        amount_wei: int = 0,
        buyer_wallet: str | None = None,
        seller_wallet: str | None = None,
    ) -> dict[str, Any]:
        buyer_address = buyer_wallet or buyer
        seller_address = seller_wallet or seller

        if not buyer_address:
            raise CampusOSException(
                "Buyer wallet address is required for escrow creation.",
                status_code=400,
            )

        if not seller_address:
            raise CampusOSException(
                "Seller wallet address is required for escrow creation.",
                status_code=400,
            )

        return self._create_escrow_sync(
            order_id,
            buyer_address,
            seller_address,
            amount_wei,
        )

    def deposit_sync(self, order_id: str, amount_wei: int) -> dict[str, Any]:
        return self._deposit_sync(order_id, amount_wei)

    def release_sync(self, order_id: str) -> dict[str, Any]:
        return self._release_sync(order_id)

    def refund_sync(self, order_id: str) -> dict[str, Any]:
        return self._refund_sync(order_id)

    def cancel_sync(self, order_id: str) -> dict[str, Any]:
        return self._cancel_sync(order_id)

    def dispute_sync(self, order_id: str) -> dict[str, Any]:
        return self._dispute_sync(order_id)

    def resolveDispute_sync(
        self, order_id: str, favor_seller: bool
    ) -> dict[str, Any]:
        return self._resolve_dispute_sync(order_id, favor_seller)

    def refundAfterTimeout_sync(self, order_id: str) -> dict[str, Any]:
        return self._refund_after_timeout_sync(order_id)


# Singleton instance for service injection across CampusOS backend
quai_blockchain_service = QuaiBlockchainService()
mock_blockchain_service = quai_blockchain_service
