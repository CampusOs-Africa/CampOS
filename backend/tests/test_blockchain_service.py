import pytest
from web3 import Web3

from app.services.blockchain_service import (
    MockBlockchainService,
    QuaiBlockchainService,
)


@pytest.mark.asyncio
async def test_blockchain_service_lifecycle():
    service = MockBlockchainService()
    user_id = "user-1234-5678"

    # 1. Verify initially unverified
    initial_is_verif = await service.isVerified(user_id)
    assert initial_is_verif is False
    initial_hash = await service.getCredentialHash(user_id)
    assert initial_hash is None

    # 2. Create credential hash (SHA-256)
    cred_hash = service.createCredentialHash(
        user_id=user_id,
        email="amina.bello@unijos.edu.ng",
        student_id_url="https://res.cloudinary.com/test/id.jpg",
        admission_letter_url="https://res.cloudinary.com/test/letter.pdf",
    )
    assert len(cred_hash) == 64  # SHA-256 hex digest length

    # 3. Store on-chain via registerStudent
    receipt = await service.registerStudent(user_id, cred_hash)
    assert receipt["user_id"] == user_id
    assert receipt["credential_hash"] == cred_hash
    assert receipt["status"] == "verified"
    assert receipt["tx_hash"].startswith("0xquai_")

    # 4. Verify after storing via isVerified & getCredentialHash
    assert await service.isVerified(user_id) is True
    assert await service.getCredentialHash(user_id) == cred_hash

    # 5. Revoke credential via revokeStudent
    revoked = await service.revokeStudent(user_id)
    assert revoked["status"] == "revoked"
    assert await service.isVerified(user_id) is False

    # 6. Re-verify student on-chain via verifyStudent
    reverified = await service.verifyStudent(user_id)
    assert reverified["status"] == "verified"
    assert await service.isVerified(user_id) is True


@pytest.mark.asyncio
async def test_quai_blockchain_service_address_resolution_and_fallback():
    service = QuaiBlockchainService()

    # 1. Test UUID address resolution
    uuid_str = "e812d4d8-4f81-4322-87f5-a7b3b3a0e1c2"
    resolved_evm = service._resolve_evm_address(uuid_str)
    assert Web3.is_address(resolved_evm)
    assert Web3.is_checksum_address(resolved_evm)

    # 2. Test direct EVM address resolution
    evm_str = "0x1234567890123456789012345678901234567890"
    resolved_direct = service._resolve_evm_address(evm_str)
    assert Web3.is_address(resolved_direct)
    assert Web3.to_checksum_address(evm_str) == resolved_direct

    # 3. Test QuaiBlockchainService full async contract methods
    cred_hash = service.createCredentialHash(
        user_id=uuid_str,
        email="student@unijos.edu.ng",
        student_id_url="https://res.cloudinary.com/id.pdf",
        admission_letter_url="https://res.cloudinary.com/letter.pdf",
    )
    res = await service.registerStudent(uuid_str, cred_hash)
    assert res["status"] == "verified"
    assert res["tx_hash"].startswith("0xquai_")
    assert res["block_number"] >= 1

    assert await service.isVerified(uuid_str) is True
    assert await service.getCredentialHash(uuid_str) == cred_hash

    rev = await service.revokeStudent(uuid_str)
    assert rev["status"] == "revoked"
    assert await service.isVerified(uuid_str) is False

    ver = await service.verifyStudent(uuid_str)
    assert ver["status"] == "verified"
    assert await service.isVerified(uuid_str) is True
