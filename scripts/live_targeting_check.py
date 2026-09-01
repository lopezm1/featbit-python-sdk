"""Evaluate caller-supplied users against a live FeatBit flag.

Set FEATBIT_TARGET_USERS to a JSON array of FeatBit user dictionaries.  The
script does not print the environment secret or modify the supplied users.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fbclient.client import FBClient  # noqa: E402
from fbclient.config import Config  # noqa: E402


def main():
    secret = os.environ.get("FEATBIT_ENV_SECRET")
    users_json = os.environ.get("FEATBIT_TARGET_USERS")
    if not secret:
        raise SystemExit("FEATBIT_ENV_SECRET is required")
    if not users_json:
        raise SystemExit("FEATBIT_TARGET_USERS is required (JSON array)")

    try:
        users = json.loads(users_json)
    except json.JSONDecodeError as exc:
        raise SystemExit("FEATBIT_TARGET_USERS must be valid JSON: %s" % exc)
    if not isinstance(users, list) or not users or not all(isinstance(user, dict) for user in users):
        raise SystemExit("FEATBIT_TARGET_USERS must be a non-empty JSON array of objects")

    event_url = os.environ.get("FEATBIT_EVENT_URL", "https://app-eval.featbit.co")
    streaming_url = os.environ.get("FEATBIT_STREAMING_URL", "wss://app-eval.featbit.co")
    flag_key = os.environ.get("FEATBIT_FLAG_KEY", "python-app-release")
    timeout = float(os.environ.get("FEATBIT_START_WAIT_SECONDS", "15"))

    client = FBClient(Config(secret, event_url=event_url, streaming_url=streaming_url),
                      start_wait=timeout)
    try:
        if not client.initialize:
            raise SystemExit("FeatBit SDK did not become ready")
        evaluations = []
        for user in users:
            detail = client.variation_detail(flag_key, user, False)
            evaluations.append({
                "user_key": user.get("key"),
                "variation": detail.variation,
                "variation_id": detail.variation_id,
                "reason": detail.reason,
            })
        print(json.dumps({"flag_key": flag_key, "evaluations": evaluations},
                         indent=2, sort_keys=True, default=str))
    finally:
        client.stop()
        client.stop()


if __name__ == "__main__":
    main()
