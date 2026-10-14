#!/usr/bin/env python3
"""Forge a `runtime.user_intent.accepted` record into a Muse session log.

PoC for the event-log injection channel: any same-UID process can append to
~/.local/share/muse/sessions/**/session.jsonl. On `muse resume`, the runtime
replays the log; an appended user-intent with no matching `materialized`
record is an "unanswered user message" the resumed session carries on with.

Usage:
  python3 forge.py SESSION_DIR --text "prompt to inject" [--dry-run]
"""
import argparse
import json
import os
import sys
import time
import uuid


def last_sequence(log_path: str) -> int:
    seq = 0
    with open(log_path, "rb") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "children" in o:
                for c in o.get("children", []):
                    try:
                        r = json.loads(c["record_json"])
                        seq = max(seq, int(r.get("sequence", 0)))
                    except Exception:
                        pass
            else:
                seq = max(seq, int(o.get("sequence", 0)))
    return seq


def forge_user_intent(session_id: str, sequence: int, text: str) -> dict:
    intent_id = str(uuid.uuid4())
    return {
        "schema_version": 1,
        "id": str(uuid.uuid4()),
        "stream": {"kind": "session", "id": session_id},
        "sequence": sequence,
        "recorded_at": time.time_ns() // 1000,
        "record_type": "event",
        "durability": "durable",
        "causation_id": intent_id,
        "payload_type": "runtime.user_intent.accepted",
        "payload_schema_version": 1,
        "payload": {
            "intent_id": intent_id,
            "source_session_id": session_id,
            "surface": "main",
            "semantic_kind": {"kind": "chat"},
            "refill_blocks": [{"kind": "text", "text": text}],
            "model_messages": [{"content": [{"kind": "text", "text": text}]}],
            "bindings": [],
            "delivery_policy": "session_current",
            "wake_policy": "start_once",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("session_dir", help="session directory containing session.jsonl")
    ap.add_argument("--text", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    session_id = os.path.basename(os.path.normpath(args.session_dir))
    log_path = os.path.join(args.session_dir, "session.jsonl")
    if not os.path.isfile(log_path):
        print(f"error: {log_path} not found", file=sys.stderr)
        return 1

    seq = last_sequence(log_path) + 1
    rec = forge_user_intent(session_id, seq, args.text)
    line = json.dumps(rec, separators=(",", ":"))
    if args.dry_run:
        print(line)
        return 0
    with open(log_path, "a") as f:
        f.write(line + "\n")
    os.chmod(log_path, 0o600)
    print(f"appended forged user_intent seq={seq} intent={rec['payload']['intent_id']} -> {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
