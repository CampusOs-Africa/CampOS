
from tests.conftest import promote_to_admin, register_and_token


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "CampusOS" in data["service"]


def test_full_api_verification_lifecycle(client, db_session):
    # 1. Register student and admin via real auth.
    student, stoken = register_and_token(
        client, "chidi.okafor@unijos.edu.ng", "Chidi Okafor"
    )
    student_id = student["id"]
    sauth = {"Authorization": f"Bearer {stoken}"}

    admin, atoken = register_and_token(
        client, "adebayo@unijos.edu.ng", "Prof. Adebayo"
    )
    admin_id = admin["id"]
    promote_to_admin(db_session, admin_id)
    aauth = {"Authorization": f"Bearer {atoken}"}

    # 2. Initial status (student reading own status).
    status_res = client.get(f"/api/v1/verification/status/{student_id}", headers=sauth)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["verification_status"] == "pending"
    assert status_data["trust_score"] == 50

    # Unverified user cannot generate QR.
    qr_unverified_res = client.get(f"/api/v1/verification/qr/{student_id}")
    assert qr_unverified_res.status_code == 400
    assert "must possess an approved Verified Student Identity" in qr_unverified_res.json()["error"]["message"]

    # 3. Upload verification documents (JWT identifies the student).
    upload_res = client.post(
        "/api/v1/verification/upload",
        headers=sauth,
        data={"university_email": "chidi.okafor@unijos.edu.ng"},
        files=[
            ("student_id", ("student_id.pdf", b"%PDF-1.4 mock id", "application/pdf")),
            ("admission_letter", ("admission.pdf", b"%PDF-1.4 mock letter", "application/pdf")),
        ],
    )
    assert upload_res.status_code == 201
    verif = upload_res.json()
    verif_id = verif["id"]
    assert verif["status"] == "pending"
    assert verif["user_id"] == student_id
    assert verif["student_id_url"].startswith("mock-storage://")

    # 4. Admin queue requires admin.
    queue_res = client.get("/api/v1/verification/admin/queue", headers=aauth)
    assert queue_res.status_code == 200
    queue = queue_res.json()
    assert len(queue) == 1
    assert queue[0]["id"] == verif_id

    # 5. Admin approve (admin identity from JWT, not query string).
    approve_res = client.post(
        f"/api/v1/verification/admin/{verif_id}/approve", headers=aauth
    )
    assert approve_res.status_code == 200
    approved_verif = approve_res.json()
    assert approved_verif["status"] == "approved"
    assert approved_verif["approved_by"] == admin_id
    assert approved_verif["credential_hash"] is not None

    # 6. Status & trust score.
    status_after = client.get(
        f"/api/v1/verification/status/{student_id}", headers=sauth
    ).json()
    assert status_after["verification_status"] == "verified"
    assert status_after["trust_score"] == 60
    assert status_after["credential_hash"] == approved_verif["credential_hash"]

    # 7. History.
    history_res = client.get(
        f"/api/v1/verification/history/{student_id}", headers=sauth
    )
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 2
    assert history[0]["new_status"] == "approved"
    assert history[1]["new_status"] == "pending"

    # 8. Blockchain credential.
    blockchain_res = client.get(f"/api/v1/verification/blockchain/{student_id}")
    assert blockchain_res.status_code == 200
    blockchain_data = blockchain_res.json()
    assert blockchain_data["is_verified"] is True
    assert blockchain_data["credential_hash"] == approved_verif["credential_hash"]
    assert "0xquai_" in blockchain_data["tx_hash"]

    # 9. Signed QR.
    qr_res = client.get(f"/api/v1/verification/qr/{student_id}")
    assert qr_res.status_code == 200
    qr_payload = qr_res.json()
    assert qr_payload["user_id"] == student_id
    assert qr_payload["status"] == "verified"
    assert len(qr_payload["signature"]) == 64

    # 10. Scan QR.
    scan_res = client.post(
        "/api/v1/verification/qr/scan",
        json={"payload": qr_payload},
    )
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["valid"] is True
    assert scan_data["user_id"] == student_id
    assert scan_data["on_chain_status"] == "verified"
    assert "Cryptographic Signature" in scan_data["verified_by"]
