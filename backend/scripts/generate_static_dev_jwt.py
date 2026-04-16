#!/usr/bin/env python3
"""Generate a long-lived JWT for local development.

Usage:
  python scripts/generate_static_dev_jwt.py --secret "<JWT_SECRET>" --user-id "<USER_ID>"

Optional:
  --email dev@hexallabs.local
  --name "Dev User"
  --days 3650
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from jose import jwt

ALGORITHM = "HS256"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a long-lived static dev JWT")
    parser.add_argument("--secret", required=True, help="JWT secret value")
    parser.add_argument("--user-id", required=True, help="User ID to set as sub claim")
    parser.add_argument("--email", default="dev@hexallabs.local", help="Email claim")
    parser.add_argument("--name", default="Dev User", help="Name claim")
    parser.add_argument(
        "--days",
        type=int,
        default=3650,
        help="Token validity in days (default: 3650 ~= 10 years)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    exp = int((datetime.now(timezone.utc) + timedelta(days=args.days)).timestamp())
    payload = {
        "sub": args.user_id,
        "email": args.email,
        "name": args.name,
        "exp": exp,
    }
    token = jwt.encode(payload, args.secret, algorithm=ALGORITHM)
    print(token)


if __name__ == "__main__":
    main()
