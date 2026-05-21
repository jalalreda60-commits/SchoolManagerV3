"""
Database initialization and default data seeding
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import init_database, User, Setting, Student, Employee
from datetime import datetime
import hashlib


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def seed_database():
    engine, session = init_database()

    # Create default admin user
    if not session.query(User).filter_by(username="admin").first():
        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="Admin",
            full_name="Administrateur Principal",
            email="admin@leschema.ma",
            is_active=True
        )
        session.add(admin)

    if not session.query(User).filter_by(username="comptable").first():
        comptable = User(
            username="comptable",
            password_hash=hash_password("compta123"),
            role="Comptable",
            full_name="Comptable Principal",
            email="comptable@leschema.ma",
            is_active=True
        )
        session.add(comptable)

    if not session.query(User).filter_by(username="secretaire").first():
        sec = User(
            username="secretaire",
            password_hash=hash_password("sec123"),
            role="Secrétaire",
            full_name="Secrétaire Principal",
            email="secretaire@leschema.ma",
            is_active=True
        )
        session.add(sec)

    # Default settings
    defaults = {
        "school_name": "Le Schéma",
        "school_slogan": "Innover - Créer - Exceller",
        "school_address": "Maroc",
        "school_phone": "+212 000-000000",
        "school_email": "contact@leschema.ma",
        "school_website": "www.leschema.ma",
        "currency": "MAD",
        "insurance_fee": "500",
        "transport_fee": "300",
        "current_year": "2025-2026",
        "receipt_counter": "0",
        "auto_backup": "true",
        "backup_days": "7",
    }

    for key, value in defaults.items():
        if not session.query(Setting).filter_by(key=key).first():
            session.add(Setting(key=key, value=value))

    session.commit()
    session.close()
    print("Database seeded successfully")


if __name__ == "__main__":
    seed_database()
