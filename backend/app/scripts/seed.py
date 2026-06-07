from pathlib import Path

from app.core.config import settings
from app.core.security import hash_password
from app.db.models import Role, User
from app.db.session import SessionLocal

USERS = [
    ("admin@example.com", "LocalAdmin123!", Role.admin),
    ("analyst@example.com", "LocalAnalyst123!", Role.analyst),
    ("reviewer@example.com", "LocalReviewer123!", Role.reviewer),
    ("viewer@example.com", "LocalViewer123!", Role.viewer),
]


def main() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        for email, password, role in USERS:
            existing = db.query(User).filter(User.email == email).one_or_none()
            if existing:
                existing.role = role
            else:
                db.add(User(email=email, hashed_password=hash_password(password), role=role))
        db.commit()
        print("Seeded demo users. Passwords are local demo credentials only.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

