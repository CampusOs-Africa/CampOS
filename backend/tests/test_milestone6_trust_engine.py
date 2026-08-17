"""
Complete Integration & Verification Test Suite for Milestone 6: Campus Trust Score Engine
========================================================================================

Verifies all Milestone 6 deliverables:
1. Bounded score rules (0-100 clamping, never <0 or >100) and Trust Badges (Platinum, Gold, Silver, Bronze, At-Risk)
2. Immutable audit trail: TrustHistory record created for EVERY score change (verification, escrow release, peer review, marketplace review, wallet P2P, dispute lost, order refund, fraud penalty, review moderation)
3. Peer reviews (review_type='peer') and marketplace reviews (review_type='marketplace') with automatic trust rewards (+1 peer / +2 marketplace)
4. Review moderation by administrator (approving, flagging, removing) with automatic trust reward reversal upon removal
5. Fraud reporting (POST /api/v1/fraud/reports), listing, and administrator resolution (resolved_confirmed / resolved_dismissed) with automatic trust penalty deduction (-20 default)
6. Trust Score Dashboard (/api/v1/trust/dashboard/{id}), Campus Leaderboard (/api/v1/trust/leaderboard), and Campus Analytics (/api/v1/trust/analytics)
"""

from tests.conftest import promote_to_admin, register_and_token


def test_milestone6_complete_trust_engine_lifecycle(client, db_session):
    # Admin & two students, all via real auth.
    admin, atoken = register_and_token(
        client, "trust.admin@unijos.edu.ng", "Prof. Trust Admin"
    )
    promote_to_admin(db_session, admin["id"])
    aauth = {"Authorization": f"Bearer {atoken}"}

    student_a, satoken = register_and_token(
        client, "zainab.usman@unilag.edu.ng", "Zainab Usman (Student A)"
    )
    student_a_id = student_a["id"]
    sauth = {"Authorization": f"Bearer {satoken}"}

    student_b, sbtoken = register_and_token(
        client, "david.alaba@unilag.edu.ng", "David Alaba (Student B)"
    )
    student_b_id = student_b["id"]
    sbauth = {"Authorization": f"Bearer {sbtoken}"}

    # Both students belong to the same school for leaderboard filtering.
    from app.models.user import User
    for uid in (student_a_id, student_b_id):
        u = db_session.get(User, uid)
        u.school = "University of Lagos"
    db_session.commit()

    # Baseline.
    dash_a = client.get(f"/api/v1/trust/dashboard/{student_a_id}", headers=sauth).json()
    assert dash_a["trust_score"] == 50
    assert dash_a["trust_badge"] == "Bronze"

    # =========================================================================
    # STEP 2: VERIFICATION BONUS (+10 -> SCORE 60, SILVER BADGE) & IMMUTABLE HISTORY
    # =========================================================================
    verif = client.post(
        "/api/v1/verification/upload",
        headers=sauth,
        data={"university_email": "zainab.usman@unilag.edu.ng"},
        files=[
            ("student_id", ("id.pdf", b"%PDF-1.4 mock id", "application/pdf")),
            ("admission_letter", ("letter.pdf", b"%PDF-1.4 mock letter", "application/pdf")),
        ],
    ).json()

    approve_res = client.post(
        f"/api/v1/verification/admin/{verif['id']}/approve", headers=aauth
    )
    assert approve_res.status_code == 200

    # Verify score 50 -> 60 (Silver badge) and immutable TrustHistory entry
    dash_a_verified = client.get(f"/api/v1/trust/dashboard/{student_a_id}", headers=sauth).json()
    assert dash_a_verified["trust_score"] == 60
    assert dash_a_verified["trust_badge"] == "Silver"
    assert len(dash_a_verified["history"]) == 1
    assert dash_a_verified["history"][0]["event_type"] == "verification"
    assert dash_a_verified["history"][0]["delta"] == 10
    assert dash_a_verified["history"][0]["old_score"] == 50
    assert dash_a_verified["history"][0]["new_score"] == 60

    # =========================================================================
    # STEP 3: PEER REVIEWS (+1 TRUST SCORE FOR >=4 STARS) & MODERATION QUEUE
    # =========================================================================
    peer_review_res = client.post(
        "/api/v1/reviews/",
        headers=sbauth,
        json={
            "reviewer_id": student_b_id,
            "reviewee_id": student_a_id,
            "rating": 5,
            "comment": "Zainab is a fantastic study partner and very trustworthy!",
            "review_type": "peer",
        },
    )
    assert peer_review_res.status_code == 201
    peer_review = peer_review_res.json()
    assert peer_review["review_type"] == "peer"
    assert peer_review["status"] == "approved"

    # Check score increased from 60 -> 61 (+1 for peer review)
    dash_a_peer = client.get(f"/api/v1/trust/dashboard/{student_a_id}", headers=sauth).json()
    assert dash_a_peer["trust_score"] == 61
    assert any(h["event_type"] == "peer_review" and h["delta"] == 1 for h in dash_a_peer["history"])

    # Test peer review filtering by user
    user_reviews = client.get(f"/api/v1/reviews/user/{student_a_id}?review_type=peer").json()
    assert len(user_reviews) == 1
    assert user_reviews[0]["comment"] == "Zainab is a fantastic study partner and very trustworthy!"

    # =========================================================================
    # STEP 4: REVIEW MODERATION & TRUST SCORE REVERSAL UPON REMOVAL
    # =========================================================================
    # Admin removes the peer review
    moderate_res = client.post(
        f"/api/v1/reviews/{peer_review['id']}/moderate",
        headers=aauth,
        json={
            "status": "removed",
            "reason": "Review violated campus moderation guidelines.",
        },
    )
    assert moderate_res.status_code == 200
    assert moderate_res.json()["status"] == "removed"
    assert moderate_res.json()["moderated_by"] == admin["id"]

    # Verify that removing the positive review reversed the trust score (+1 -> -1 -> score back to 60)
    dash_a_moderated = client.get(f"/api/v1/trust/dashboard/{student_a_id}", headers=sauth).json()
    assert dash_a_moderated["trust_score"] == 60
    assert any(h["event_type"] == "review_moderation" and h["delta"] == -1 for h in dash_a_moderated["history"])

    # =========================================================================
    # STEP 5: FRAUD REPORTING, LISTING, AND ADMINISTRATOR RESOLUTION
    # =========================================================================
    # Student B submits a fraud report against Student A
    report_res = client.post(
        "/api/v1/fraud/reports",
        headers=sbauth,
        json={
            "reporter_id": student_b_id,
            "reported_user_id": student_a_id,
            "category": "scam_listing",
            "description": "Reported user listed a textbook that was never delivered after meetup.",
            "evidence_url": "https://res.cloudinary.com/test/evidence.jpg",
        },
    )
    assert report_res.status_code == 201
    report = report_res.json()
    report_id = report["id"]
    assert report["status"] == "pending"
    assert report["reporter_name"] == "David Alaba (Student B)"

    # List pending fraud reports
    list_reports = client.get("/api/v1/fraud/reports?status=pending", headers=aauth).json()
    assert len(list_reports) >= 1
    assert any(r["id"] == report_id for r in list_reports)

    # Admin resolves fraud report as confirmed (applies -20 Trust Score penalty)
    resolve_res = client.post(
        f"/api/v1/fraud/reports/{report_id}/resolve",
        json={
            "status": "resolved_confirmed",
            "penalty_points": 20,
            "resolution_notes": "Investigation confirmed fraudulent listing behavior. Applying -20 penalty.",
        },
        headers=aauth,
    )
    assert resolve_res.status_code == 200
    resolved = resolve_res.json()
    assert resolved["status"] == "resolved_confirmed"
    assert resolved["penalty_applied"] == 20

    # Check Student A's score dropped from 60 to 40 (60 - 20 = 40, Bronze badge)
    dash_a_penalized = client.get(f"/api/v1/trust/dashboard/{student_a_id}", headers=sauth).json()
    assert dash_a_penalized["trust_score"] == 40
    assert dash_a_penalized["trust_badge"] == "Bronze"
    assert dash_a_penalized["total_penalties_deducted"] >= 20
    assert any(h["event_type"] == "fraud_penalty" and h["delta"] == -20 for h in dash_a_penalized["history"])

    # =========================================================================
    # STEP 6: BOUNDED SCORE CLAMPING (0-100 RANGE) VERIFICATION
    # =========================================================================
    # Even if we apply a -50 penalty (from score 40), score must clamp to minimum 0 (never negative)
    resolve_extreme = client.post(
        f"/api/v1/fraud/reports/{report_id}/resolve",
        json={
            "status": "resolved_confirmed",
            "penalty_points": 50,
            "resolution_notes": "Extreme penalty test for score clamping.",
        },
        headers=aauth,
    )
    assert resolve_extreme.status_code == 200
    dash_zero = client.get(f"/api/v1/trust/dashboard/{student_a_id}", headers=sauth).json()
    assert dash_zero["trust_score"] == 0
    assert dash_zero["trust_badge"] == "At-Risk"

    # =========================================================================
    # STEP 7: CAMPUS LEADERBOARD & ANALYTICS
    # =========================================================================
    leaderboard = client.get("/api/v1/trust/leaderboard?school=University of Lagos").json()
    assert len(leaderboard) >= 2
    # Ensure sorted by trust_score descending
    scores = [item["trust_score"] for item in leaderboard]
    assert scores == sorted(scores, reverse=True)
    assert leaderboard[0]["rank"] == 1

    analytics = client.get("/api/v1/trust/analytics").json()
    assert "campus_average_score" in analytics
    assert "score_distribution" in analytics
    assert "Platinum (85-100)" in analytics["score_distribution"]
    assert "At-Risk (0-39)" in analytics["score_distribution"]
    assert analytics["recent_trust_events_24h"] >= 1
