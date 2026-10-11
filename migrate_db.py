"""Database migration and verification script for PlayWithPDFs.

Usage:
    python migrate_db.py
    python migrate_db.py --url "postgresql://user:pass@host:5432/dbname?sslmode=require"
"""

import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()


def get_target_url(override_url=None):
    raw = override_url or os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_CONNECTION_KEY")
    if not raw:
        print("[!] No PostgreSQL connection key found in environment or arguments.")
        return None

    if raw.startswith("postgres://"):
        raw = raw.replace("postgres://", "postgresql+psycopg://", 1)
    elif raw.startswith("postgresql://") and not raw.startswith("postgresql+"):
        raw = raw.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw


def test_connection(target_url):
    print(f"[*] Testing connection to: {target_url.split('@')[-1] if '@' in target_url else target_url}")
    from sqlalchemy import create_engine, text

    try:
        engine = create_engine(
            target_url,
            connect_args={"connect_timeout": 5},
            pool_pre_ping=True
        )
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();")).scalar()
            print("[+] Connection successful!")
            print(f"[+] Server version: {result}")
        engine.dispose()
        return True
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        return False


def run_migration(target_url):
    print("\n[*] Initializing tables via Flask-SQLAlchemy...")
    from flask import Flask
    from extensions import db
    import models
    from utils.tracking import seed_tools

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = target_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
        print("[+] Tables created successfully (admin_users, tool_configs, tool_events, contact_messages, audit_logs).")

        # Check if local SQLite exists and migrate records if Postgres is empty
        sqlite_path = os.path.join(app.instance_path, "playwithpdfs.db")
        if not os.path.exists(sqlite_path):
            sqlite_path = "playwithpdfs.db"

        if os.path.exists(sqlite_path):
            print(f"[*] Found local SQLite database at: {sqlite_path}")
            import sqlite3
            s_conn = sqlite3.connect(sqlite_path)
            s_cur = s_conn.cursor()

            # 1. Admin Users
            try:
                existing_admins = models.AdminUser.query.count()
                if existing_admins == 0:
                    s_cur.execute("SELECT email, name, password_hash, role, is_active FROM admin_users")
                    admins = s_cur.fetchall()
                    for email, name, pwd, role, active in admins:
                        user = models.AdminUser(
                            email=email, name=name, password_hash=pwd, role=role, is_active=bool(active)
                        )
                        db.session.add(user)
                    db.session.commit()
                    print(f"[+] Migrated {len(admins)} admin user(s) from SQLite.")
                else:
                    print(f"[i] PostgreSQL already has {existing_admins} admin user(s). Skipping admin migration.")
            except Exception as e:
                db.session.rollback()
                print(f"[!] Note on admin users migration: {e}")

            # 2. End-Users
            try:
                existing_users = models.User.query.count()
                if existing_users == 0:
                    # check if department column exists in sqlite
                    s_cur.execute("PRAGMA table_info(users)")
                    cols = [row[1] for row in s_cur.fetchall()]
                    if "department" in cols:
                        s_cur.execute("SELECT name, email, department, password_hash, is_active FROM users")
                        users_data = s_cur.fetchall()
                        for name, email, dept, pwd, active in users_data:
                            u = models.User(
                                name=name, email=email, department=dept or "General / Other", password_hash=pwd, is_active=bool(active)
                            )
                            db.session.add(u)
                    else:
                        s_cur.execute("SELECT name, email, password_hash, is_active FROM users")
                        users_data = s_cur.fetchall()
                        for name, email, pwd, active in users_data:
                            u = models.User(
                                name=name, email=email, department="General / Other", password_hash=pwd, is_active=bool(active)
                            )
                            db.session.add(u)
                    db.session.commit()
                    print(f"[+] Migrated {len(users_data)} end-user(s) with departments from SQLite.")
            except Exception as e:
                db.session.rollback()
                print(f"[!] Note on end-users migration: {e}")

            # 3. Tool configs
            seed_count = seed_tools(app)
            print(f"[+] Seeded {seed_count} tool configuration(s).")

            s_conn.close()
        else:
            seed_count = seed_tools(app)
            print(f"[+] Seeded {seed_count} tool configuration(s).")

    print("\n[✔] Database setup and migration completed successfully!")


def main():
    parser = argparse.ArgumentParser(description="Test and migrate database for PlayWithPDFs")
    parser.add_argument("--url", help="Database connection URL", default=None)
    args = parser.parse_args()

    target_url = get_target_url(args.url)
    if not target_url:
        print("[!] Exiting: No database URL provided.")
        sys.exit(1)

    if not test_connection(target_url):
        print("\n[!] The target database is currently unreachable.")
        print("[!] If you are using a hosted provider, ensure the database instance is active, not paused, and DNS resolves.")
        sys.exit(1)

    run_migration(target_url)


if __name__ == "__main__":
    main()
