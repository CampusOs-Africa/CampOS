import pytest

from app.core.exceptions import CampusOSException
from app.models.user import User
from app.schemas.wallet import WalletConnectRequest, WalletSendRequest
from app.services.wallet_service import WalletService


@pytest.mark.asyncio
async def test_wallet_connection_and_faucet(db_session):
    user = User(
        id="student-wallet-01",
        name="Amina Bello",
        email="amina@unijos.edu.ng",
        role="student",
    )
    db_session.add(user)
    db_session.commit()

    service = WalletService(db=db_session)

    # 1. Test connecting wallet with mock signature
    connect_req = WalletConnectRequest(
        user_id="student-wallet-01",
        wallet_address="0x1111111111111111111111111111111111111111",
        message="Sign in to CampusOS",
        signature="0xmock_signature_hex_digest_65_bytes",
    )
    res = await service.connect_wallet(connect_req)
    assert res.verified is True
    assert res.wallet_address == "0x1111111111111111111111111111111111111111"

    # Check that user profile is updated
    db_session.refresh(user)
    assert user.wallet_address == "0x1111111111111111111111111111111111111111"

    # 2. Check balance calculation
    bal = await service.get_balance(user_id="student-wallet-01")
    assert bal.balance_quai > 0
    assert bal.fiat_value_ngn == round(bal.balance_quai * 1500.0, 2)

    # 3. Check welcome faucet transaction created in history
    history = service.get_history("student-wallet-01")
    assert len(history) == 1
    assert history[0].type == "faucet"
    assert history[0].amount == 25.0


@pytest.mark.asyncio
async def test_send_quai_p2p_transfer(db_session):
    sender = User(
        id="sender-01",
        name="Chidi Okafor",
        email="chidi@unijos.edu.ng",
        wallet_address="0x2222222222222222222222222222222222222222",
    )
    receiver = User(
        id="receiver-01",
        name="Ngozi Eze",
        email="ngozi@unijos.edu.ng",
        wallet_address="0x3333333333333333333333333333333333333333",
    )
    db_session.add(sender)
    db_session.add(receiver)
    db_session.commit()

    service = WalletService(db=db_session)

    # Send 5.0 QUAI from Chidi to Ngozi by email address
    send_req = WalletSendRequest(
        sender_id="sender-01",
        recipient="ngozi@unijos.edu.ng",
        amount_quai=5.0,
        note="Textbook split payment",
    )
    res = await service.send_quai(send_req)
    assert res.success is True
    assert res.amount_quai == 5.0
    assert "0x3333" in res.recipient

    # Check sender history
    sender_history = service.get_history("sender-01")
    assert any(tx.type == "send" and tx.amount == 5.0 for tx in sender_history)

    # Check receiver history
    recv_history = service.get_history("receiver-01")
    assert any(tx.type == "receive" and tx.amount == 5.0 for tx in recv_history)


@pytest.mark.asyncio
async def test_invalid_wallet_address_rejection(db_session):
    user = User(id="invalid-user-01", name="Test", email="test@test.org")
    db_session.add(user)
    db_session.commit()

    service = WalletService(db=db_session)
    with pytest.raises(CampusOSException) as exc_info:
        await service.connect_wallet(
            WalletConnectRequest(
                user_id="invalid-user-01",
                wallet_address="not-an-evm-address",
                message="test",
                signature="0xmock",
            )
        )
    assert exc_info.value.status_code == 400
    assert "Invalid Quai EVM wallet address" in exc_info.value.message
