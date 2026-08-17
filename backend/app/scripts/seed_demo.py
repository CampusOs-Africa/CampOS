#!/usr/bin/env python3
"""
CampusOS Local & Hackathon Demo Seeder
--------------------------------------
Pre-seeds the relational SQLite / PostgreSQL database with required demo user accounts,
welcome faucet transactions, verified student seller profiles, and default marketplace
listings so that local development and hackathon demo dashboards render cleanly without
404 errors.

Idempotent: Safe to run repeatedly on startup.
"""

import logging
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_secret
from app.models.marketplace import MarketplaceCategory, MarketplaceListing
from app.models.transaction import Transaction
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("campusos.seed_demo")


def seed_demo_database() -> None:
    logger.info(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Demo Student for Verification & QR Identity Dashboards
        u1 = db.query(User).filter_by(id="student-demo-001").first()
        if not u1:
            u1 = User(
                id="student-demo-001",
                name="Amina Bello (Demo Student)",
                email="amina.demo@unn.edu.ng",
                role="student",
                school="University of Nigeria, Nsukka",
                faculty="Engineering",
                department="Computer Science",
                trust_score=50,
                verification_status="pending",
                created_at=datetime.now(timezone.utc),
            )
            db.add(u1)
            logger.info("Created user: student-demo-001 (Amina Bello)")

        # 2. Seed Demo Student for Campus Wallet Dashboard
        u2 = db.query(User).filter_by(id="student-wallet-01").first()
        if not u2:
            u2 = User(
                id="student-wallet-01",
                name="Chidi Okafor (Demo Wallet)",
                email="chidi.demo@unijos.edu.ng",
                role="student",
                school="University of Jos",
                faculty="Natural Sciences",
                department="Computer Science",
                wallet_address="0x71c0000000000000000000000000000000000001",
                trust_score=50,
                verification_status="pending",
                created_at=datetime.now(timezone.utc),
            )
            db.add(u2)
            logger.info("Created user: student-wallet-01 (Chidi Okafor)")

        # Add initial faucet deposit if no transactions exist for student-wallet-01
        tx_existing = (
            db.query(Transaction).filter_by(user_id="student-wallet-01").first()
        )
        if not tx_existing:
            faucet_tx = Transaction(
                id=str(uuid.uuid4()),
                user_id="student-wallet-01",
                wallet_address="0x71c0000000000000000000000000000000000001",
                recipient_address="0x71c0000000000000000000000000000000000001",
                amount=25.5,
                tx_hash="0xfaucet_welcome_demo_tx_hash_001",
                type="faucet",
                status="confirmed",
                network="Quai Network Testnet (Chain ID 9000)",
                note="Welcome Faucet Deposit (+25.5 QUAI / 38,250 NGN)",
                created_at=datetime.now(timezone.utc),
            )
            db.add(faucet_tx)
            logger.info("Created initial welcome faucet transaction for student-wallet-01")

        # 3. Seed Peer Review Partner User
        u3 = db.query(User).filter_by(id="student-peer-partner-02").first()
        if not u3:
            u3 = User(
                id="student-peer-partner-02",
                name="Emeka Nwosu",
                email="emeka.nwosu@unn.edu.ng",
                role="verified_student",
                school="University of Nigeria, Nsukka",
                faculty="Engineering",
                department="Computer Science",
                trust_score=60,
                verification_status="approved",
                created_at=datetime.now(timezone.utc),
            )
            db.add(u3)
            logger.info("Created user: student-peer-partner-02 (Emeka Nwosu)")

        # 4. Seed Admin Verification Reviewer & Moderator
        u4 = db.query(User).filter_by(id="admin-001").first()
        if not u4:
            u4 = User(
                id="admin-001",
                name="Dr. Nneka Eze (Admin Reviewer)",
                email="nneka.eze@unn.edu.ng",
                role="admin",
                school="University of Nigeria, Nsukka",
                faculty="Engineering",
                department="Computer Science",
                trust_score=100,
                verification_status="approved",
                created_at=datetime.now(timezone.utc),
            )
            db.add(u4)
            logger.info("Created user: admin-001 (Dr. Nneka Eze)")

        # 5. Seed Verified Student Seller & Default Campus Marketplace Listings
        u5 = db.query(User).filter_by(id="seller-01").first()
        if not u5:
            u5 = User(
                id="seller-01",
                name="Tunde Balogun (Verified Seller)",
                email="tunde.balogun@unilag.edu.ng",
                role="verified_student",
                school="University of Lagos",
                faculty="Engineering",
                department="Electrical Engineering",
                trust_score=75,
                verification_status="approved",
                created_at=datetime.now(timezone.utc),
            )
            db.add(u5)
            logger.info("Created user: seller-01 (Tunde Balogun)")

        # All local demo accounts share a well-known demo password so they can
        # be used with the real password login during local development.
        for _u in db.query(User).all():
            if not _u.hashed_password:
                _u.hashed_password = hash_secret("CampusOS2026!")

        # Commit users before creating listings
        db.commit()

        # Seed default campus marketplace listings if none exist for seller-01
        listing_existing = (
            db.query(MarketplaceListing).filter_by(seller_id="seller-01").first()
        )
        if not listing_existing:
            item1 = MarketplaceListing(
                id="listing-demo-001",
                seller_id="seller-01",
                category="books",
                title="Engineering Mathematics III Textbook (4th Ed)",
                description="Clean condition engineering textbook with solved past questions for 300 level students.",
                price=0.5,
                condition="like_new",
                images=[
                    "https://res.cloudinary.com/demo/image/upload/v1/campusos/textbook.jpg"
                ],
                status="active",
                inventory_count=1,
                created_at=datetime.now(timezone.utc),
            )
            db.add(item1)
            logger.info("Created listing: listing-demo-001 (Engineering Mathematics III)")
            db.commit()

        logger.info("✅ CampusOS local demo database seeding completed successfully.")

    except Exception as exc:
        db.rollback()
        logger.error(f"Error seeding demo database: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_database()
    sys.exit(0)
