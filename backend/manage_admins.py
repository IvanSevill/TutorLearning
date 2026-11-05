"""Grants or revokes the admin role from the server's command line.

No API route can do this, so a web request can never create an admin:
    python manage_admins.py grant someone@example.com
"""
import sys

import models
from database import SessionLocal

ACTIONS = {"grant": True, "revoke": False}
USAGE = "usage: python manage_admins.py grant|revoke <email>"


def main(args):
    if len(args) != 2 or args[0] not in ACTIONS:
        print(USAGE, file=sys.stderr)
        return 2

    action, email = args
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            print(f"No user with email {email}", file=sys.stderr)
            return 1
        user.is_admin = ACTIONS[action]
        db.commit()
    finally:
        db.close()

    print(f"{email} is now an admin" if ACTIONS[action] else f"{email} is no longer an admin")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
