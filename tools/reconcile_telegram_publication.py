#!/usr/bin/env python3
"""Human-only reconciliation for an ambiguous Telegram publication attempt."""

from __future__ import annotations

import argparse
from pathlib import Path

from publication_guard import PublicationLedger


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True,
                        help="Path to tg/publication-ledger.sqlite3")
    parser.add_argument("--event-key", required=True)
    parser.add_argument("--outcome", choices=("SENT", "FAILED"), required=True,
                        help="SENT only after finding the post; FAILED only after confirming it was not sent")
    parser.add_argument("--message-id", default="")
    parser.add_argument("--chat-id", default="")
    parser.add_argument("--note", required=True,
                        help="What was checked and why this outcome is certain")
    args = parser.parse_args()

    if args.outcome == "SENT" and not args.message_id:
        parser.error("--message-id is required when outcome is SENT")
    if args.outcome == "FAILED" and len(args.note.strip()) < 20:
        parser.error("A specific reconciliation note is required for FAILED")

    ledger = PublicationLedger(args.ledger)
    before = ledger.get_by_event_key(args.event_key)
    if not before:
        parser.error("event_key was not found in the ledger")
    if before["status"] not in ("SENDING", "UNKNOWN"):
        parser.error("only SENDING/UNKNOWN records can be reconciled")
    ledger.resolve_pending(args.event_key, args.outcome, args.message_id, args.chat_id, args.note)
    after = ledger.get_by_event_key(args.event_key)
    print("RECONCILED", after["event_key"], after["status"], after["message_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
