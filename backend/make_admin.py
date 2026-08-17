#!/usr/bin/env python3
r"""
make_admin.py - CampusOS user/DB maintenance (standalone, no app imports).

What it does
------------
1. Ensures the `users` table exists WITH ALL expected columns (adds any missing
   columns via ALTER TABLE — idempotent/safe).
2. Creates or promotes a REAL administrator (role='admin') with a known
   password hash, so you can log in through the normal /login form even when
   ALLOW_DEMO_LOGIN=false.
3. Backfills a DEFAULT password hash for EVERY existing user row that has no
   `hashed_password` (e.g. the seeded demo users), so they can also log in.
4. Optionally writes a BRAND-NEW database file (--new-db) that copies all
   current users, applies the schema/backfill, and adds the admin — without
   touching your original file.

Password hashing mirrors backend/app/core/security.py:hash_secret exactly:
    PBKDF2-HMAC-SHA256, salt "campusos-salt", 100000 iterations.

USAGE
-----
  # your machine (Windows example):
  python backend/scripts/make_admin.py ^
      --db "C:\Users\Acer\Downloads\CampusOS\backend\campusos.db"

  # custom admin + shared default password for backfilled users:
  python backend/scripts/make_admin.py --db "C:\...\campusos.db" \
      --email admin@campusos.ng --password "CampusOS@Admin2024" \
      --default-password "CampusOS@2024"

  # produce a new, enhanced DB file (original left untouched):
  python backend/scripts/make_admin.py --db "C:\...\campusos.db" \
      --new-db "C:\...\campusos_new.db"
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ---- paths ----------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent          # backend/scripts
BACKEND_DIR = SCRIPT_DIR.parent                        # backend
REPO_ROOT = BACKEND_DIR.parent                         # repo root

DEFAULT_EMAIL = "admin@campusos.ng"
DEFAULT_PASSWORD = "CampusOS@Admin2024"
DEFAULT_DEFAULT_PASSWORD = "CampusOS@2024"
DEFAULT_NAME = "CampusOS Administrator"

# Column -> SQL type (used both for CREATE TABLE and for ADD COLUMN when missing)
COLUMNS: dict[str, str] = {
    "id": "TEXT",
    "name": "TEXT",
    "email": "TEXT",
    "phone": "TEXT",
    "date_of_birth": "TEXT",
    "gender": "TEXT",
    "wallet_address": "TEXT",
    "student_id": "TEXT",
    "school": "TEXT",
    "faculty": "TEXT",
    "department": "TEXT",
    "level": "TEXT",
    "matric_number": "TEXT",
    "admission_year": "TEXT",
    "school_email": "TEXT",
    "trust_score": "INTEGER",
    "verification_status": "TEXT",
    "role": "TEXT",
    "hashed_password": "TEXT",
    "is_active": "INTEGER",
    "created_at": "TEXT",
}

USERS_DDL = """
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  phone TEXT,
  date_of_birth TEXT,
  gender TEXT,
  wallet_address TEXT UNIQUE,
  student_id TEXT,
  school TEXT,
  faculty TEXT,
  department TEXT,
  level TEXT,
  matric_number TEXT,
  admission_year TEXT,
  school_email TEXT,
  trust_score INTEGER NOT NULL DEFAULT 50,
  verification_status TEXT NOT NULL DEFAULT 'pending',
  role TEXT NOT NULL DEFAULT 'student',
  hashed_password TEXT,
  is_active BOOLEAN NOT NULL DEFAULT 1,
  created_at DATETIME
);
"""


def resolve_db_path(explicit: str | None) -> str:
    if explicit:
        return explicit
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("sqlite:///"):
        return url[len("sqlite:///"):]
    env_file = BACKEND_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("DATABASE_URL="):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v.startswith("sqlite:///"):
                    return v[len("sqlite:///"):]
    for c in (BACKEND_DIR / "campusos.db", REPO_ROOT / "campusos.db"):
        if c.exists():
            return str(c)
    return str(REPO_ROOT / "campusos.db")


# Mirror of backend/app/core/security.py:hash_secret
def hash_secret(secret: str, salt: str = "campusos-salt") -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", secret.encode("utf-8"), salt.encode("utf-8"), 100000
    ).hex()


def ensure_schema(conn: sqlite3.Connection) -> list[str]:
    """Create the table if missing and ADD any columns that are absent.
    Returns the list of columns that were added."""
    conn.execute(USERS_DDL)
    conn.commit()
    existing = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    added: list[str] = []
    for col, typ in COLUMNS.items():
        if col not in existing:
            # ADD COLUMN without NOT NULL to stay safe on populated tables
            conn.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
            added.append(col)
    if added:
        conn.commit()
    return added


def backfill_passwords(conn: sqlite3.Connection, default_password: str) -> int:
    """Set a default password hash for every user lacking one. Returns count."""
    pw_hash = hash_secret(default_password)
    cur = conn.execute(
        "UPDATE users SET hashed_password = ? WHERE hashed_password IS NULL OR hashed_password = ''",
        (pw_hash,),
    )
    conn.commit()
    return cur.rowcount


def create_admin(conn: sqlite3.Connection, email: str, password: str, name: str) -> None:
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    pw_hash = hash_secret(password)
    conn.execute(
        """
        INSERT INTO users
          (id, name, email, role, verification_status, hashed_password, is_active, trust_score, created_at)
        VALUES (?, ?, ?, 'admin', 'verified', ?, 1, 100, ?)
        ON CONFLICT(email) DO UPDATE SET
          role='admin',
          verification_status='verified',
          is_active=1,
          hashed_password=excluded.hashed_password,
          trust_score=100
        """,
        (user_id, name, email.lower(), pw_hash, now),
    )
    conn.commit()


def copy_users(src: sqlite3.Connection, dst: sqlite3.Connection) -> int:
    """Copy all user rows from src -> dst (common columns, IGNORE conflicts)."""
    src_cols = {r[1] for r in src.execute("PRAGMA table_info(users)").fetchall()}
    dst_cols = {r[1] for r in dst.execute("PRAGMA table_info(users)").fetchall()}
    cols = [c for c in COLUMNS if c in src_cols and c in dst_cols]
    if not cols:
        return 0
    rows = src.execute(f"SELECT {','.join(cols)} FROM users").fetchall()
    placeholders = ",".join("?" * len(cols))
    sql = f"INSERT OR IGNORE INTO users ({','.join(cols)}) VALUES ({placeholders})"
    count = 0
    for row in rows:
        dst.execute(sql, tuple(row))
        count += 1
    dst.commit()
    return count


def report(conn: sqlite3.Connection, label: str) -> None:
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    admins = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
    no_pw = conn.execute(
        "SELECT COUNT(*) FROM users WHERE hashed_password IS NULL OR hashed_password = ''"
    ).fetchone()[0]
    print(f"  [{label}] users={total}  admins={admins}  still_missing_password={no_pw}")


def main() -> None:
    ap = argparse.ArgumentParser(description="CampusOS admin + user/DB maintenance.")
    ap.add_argument("--email", default=DEFAULT_EMAIL)
    ap.add_argument("--password", default=DEFAULT_PASSWORD)
    ap.add_argument("--name", default=DEFAULT_NAME)
    ap.add_argument("--default-password", default=DEFAULT_DEFAULT_PASSWORD,
                    help="Password set for every existing user lacking a hash.")
    ap.add_argument("--db", default=None, help="Source campusos.db path.")
    ap.add_argument("--new-db", default=None,
                    help="Write a NEW enhanced DB file here (source left untouched).")
    ap.add_argument("--no-backfill", action="store_true",
                    help="Skip setting default passwords on users without one.")
    ap.add_argument("--force", action="store_true",
                    help="Allow --new-db to overwrite an existing file.")
    args = ap.parse_args()

    src_path = resolve_db_path(args.db)
    print(f"[make_admin] Source database: {src_path}")

    if args.new_db:
        new_path = args.new_db
        if os.path.exists(new_path) and not args.force:
            raise SystemExit(
                f"[make_admin] Refusing to overwrite existing --new-db '{new_path}'. "
                f"Delete it or pass --force."
            )
        print(f"[make_admin] Creating NEW database: {new_path}")
        if os.path.exists(new_path):
            os.remove(new_path)
        src = sqlite3.connect(src_path)
        try:
            src_cols_ok = src.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='users'"
            ).fetchone()[0]
            if not src_cols_ok:
                print("[make_admin] Source has no 'users' table; starting fresh.")
            new = sqlite3.connect(new_path)
            try:
                added = ensure_schema(new)
                if added:
                    print(f"[make_admin] Added missing columns to new DB: {added}")
                copied = copy_users(src, new) if src_cols_ok else 0
                print(f"[make_admin] Copied {copied} user row(s) from source.")
                if not args.no_backfill:
                    n = backfill_passwords(new, args.default_password)
                    print(f"[make_admin] Set default password on {n} user(s) in new DB.")
                create_admin(new, args.email, args.password, args.name)
                report(new, "new db")
            finally:
                new.close()
        finally:
            src.close()
        print("\nPoint the backend at the new file (or replace the old one) and start it.")
        print(f"  New DB : {new_path}")
        print(f"  Admin  : {args.email.lower()} / {args.password}")
        print(f"  Others : any user / {args.default_password}")
        return

    # ---- in-place mode ----
    conn = sqlite3.connect(src_path)
    try:
        added = ensure_schema(conn)
        if added:
            print(f"[make_admin] Added missing columns: {added}")
        if not args.no_backfill:
            n = backfill_passwords(conn, args.default_password)
            print(f"[make_admin] Set default password on {n} existing user(s).")
        create_admin(conn, args.email, args.password, args.name)
        report(conn, "db")
    finally:
        conn.close()

    print("\nLOGIN CREDENTIALS")
    print(f"  Admin : {args.email.lower()} / {args.password}")
    if not args.no_backfill:
        print(f"  Others: <their email> / {args.default_password}")
    print("\nNote: the /login form currently ignores the password field unless you apply")
    print("the one-line fix: login(email.trim(), password) in frontend/app/login/page.tsx")


if __name__ == "__main__":
    main()