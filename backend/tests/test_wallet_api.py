from tests.conftest import TEST_PASSWORD


def test_wallet_api_lifecycle(client):
    # 1. Register via the real auth flow
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Kalu Okoro",
            "email": "kalu.okoro@unilag.edu.ng",
            "password": TEST_PASSWORD,
        },
    )
    assert reg.status_code == 201
    user = reg.json()["user"]
    token = reg.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    user_id = user["id"]

    # 2. Balance endpoint requires auth; resolves to the current user.
    bal_res = client.get("/api/v1/wallet/balance", headers=auth)
    assert bal_res.status_code == 200
    bal_data = bal_res.json()
    assert bal_data["balance_quai"] > 0
    assert "Quai Network Testnet" in bal_data["network"]

    # 3. Connect Quai wallet (user_id is forced from JWT).
    connect_res = client.post(
        "/api/v1/wallet/connect",
        headers=auth,
        json={
            "user_id": user_id,
            "wallet_address": "0x4444444444444444444444444444444444444444",
            "message": "CampusOS Web3 Authentication Challenge",
            "signature": "0xmock_signature_hex_65_bytes",
        },
    )
    assert connect_res.status_code == 200
    connect_data = connect_res.json()
    assert connect_data["verified"] is True
    assert connect_data["user_id"] == user_id
    assert (
        connect_data["wallet_address"]
        == "0x4444444444444444444444444444444444444444"
    )

    # 4. History for the authenticated user.
    history_res = client.get("/api/v1/wallet/history", headers=auth)
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert len(history_data) == 1
    assert history_data[0]["type"] == "faucet"
    assert history_data[0]["amount"] == 25.0

    # 5. Send QUAI (sender is forced from JWT).
    send_res = client.post(
        "/api/v1/wallet/send",
        headers=auth,
        json={
            "sender_id": user_id,
            "recipient": "0x5555555555555555555555555555555555555555",
            "amount_quai": 3.5,
            "note": "Club event fee",
        },
    )
    assert send_res.status_code == 200
    send_data = send_res.json()
    assert send_data["success"] is True
    assert send_data["amount_quai"] == 3.5
    assert send_data["tx_hash"].startswith("0xquai_send_")

    # 6. Dashboard for the authenticated user.
    dash_res = client.get(f"/api/v1/wallet/dashboard/{user_id}", headers=auth)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert (
        dash_data["wallet_address"]
        == "0x4444444444444444444444444444444444444444"
    )
    assert dash_data["qr_receive_address"] == "quai:0x4444444444444444444444444444444444444444"
    assert len(dash_data["transactions"]) == 2  # faucet + send
