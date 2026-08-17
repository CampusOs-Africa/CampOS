
from tests.conftest import promote_to_admin, register_and_token


def test_admin_reject_and_resubmit_lifecycle(client, db_session):
    student, stoken = register_and_token(
        client, "amina.bello@unijos.edu.ng", "Amina Bello"
    )
    student_id = student["id"]
    sauth = {"Authorization": f"Bearer {stoken}"}

    admin, atoken = register_and_token(client, "admin@unijos.edu.ng", "Admin User")
    promote_to_admin(db_session, admin["id"])
    aauth = {"Authorization": f"Bearer {atoken}"}

    verif = client.post(
        "/api/v1/verification/upload",
        headers=sauth,
        data={"university_email": "amina.bello@unijos.edu.ng"},
        files=[
            ("student_id", ("id.png", b"\x89PNG\r\n\x1a\n mock id", "image/png")),
            ("admission_letter", ("letter.png", b"\x89PNG\r\n\x1a\n mock letter", "image/png")),
        ],
    ).json()
    verif_id = verif["id"]

    resubmit_res = client.post(
        f"/api/v1/verification/admin/{verif_id}/resubmit",
        headers=aauth,
        json={"reason": "Admission letter is blurry. Please re-upload a clear scanned copy."},
    )
    assert resubmit_res.status_code == 200
    assert resubmit_res.json()["status"] == "resubmission_requested"
    assert "blurry" in resubmit_res.json()["rejection_reason"]

    status1 = client.get(
        f"/api/v1/verification/status/{student_id}", headers=sauth
    ).json()
    assert status1["verification_status"] == "resubmission_requested"
    assert status1["trust_score"] == 50

    verif2 = client.post(
        "/api/v1/verification/upload",
        headers=sauth,
        data={"university_email": "amina.bello@unijos.edu.ng"},
        files=[
            ("student_id", ("id_v2.png", b"\x89PNG\r\n\x1a\n mock id v2", "image/png")),
            ("admission_letter", ("letter_v2.png", b"\x89PNG\r\n\x1a\n mock letter v2", "image/png")),
        ],
    ).json()
    verif_id2 = verif2["id"]
    assert verif2["status"] == "pending"

    reject_res = client.post(
        f"/api/v1/verification/admin/{verif_id2}/reject",
        headers=aauth,
        json={"reason": "Document appears altered."},
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "rejected"

    status2 = client.get(
        f"/api/v1/verification/status/{student_id}", headers=sauth
    ).json()
    assert status2["verification_status"] == "rejected"
    assert status2["trust_score"] == 50

    history = client.get(
        f"/api/v1/verification/history/{student_id}", headers=sauth
    ).json()
    assert len(history) == 4
    statuses = [item["new_status"] for item in history]
    assert statuses == ["rejected", "pending", "resubmission_requested", "pending"]


def test_invalid_email_domain_rejection(client):
    student, stoken = register_and_token(client, "test.student@gmail.com", "Test Student")
    sauth = {"Authorization": f"Bearer {stoken}"}

    res = client.post(
        "/api/v1/verification/upload",
        headers=sauth,
        data={"university_email": "personal@gmail.com"},
        files=[
            ("student_id", ("id.pdf", b"pdf content", "application/pdf")),
            ("admission_letter", ("letter.pdf", b"letter content", "application/pdf")),
        ],
    )
    assert res.status_code == 400
    assert "not belong to a recognized university academic domain" in res.json()["error"]["message"]
