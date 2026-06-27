#!/usr/bin/env python3
"""Check or write a local research cache entry for a topic (24-hour TTL)."""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", ".tmp", "cache")
TTL_HOURS = 24


def _slug(topic: str) -> str:
    normalized = topic.lower().strip()
    h = hashlib.md5(normalized.encode()).hexdigest()[:8]
    safe = "".join(c if c.isalnum() else "-" for c in normalized)[:40]
    return f"{safe}-{h}"


def _cache_path(topic: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{_slug(topic)}.json")


def check(topic: str) -> bool:
    path = _cache_path(topic)
    if not os.path.exists(path):
        return False
    with open(path) as f:
        entry = json.load(f)
    written_at = datetime.fromisoformat(entry["written_at"])
    if datetime.now() - written_at > timedelta(hours=TTL_HOURS):
        return False
    print(entry["data_path"])
    return True


def write(topic: str, data_path: str) -> None:
    path = _cache_path(topic)
    with open(path, "w") as f:
        json.dump({"written_at": datetime.now().isoformat(), "data_path": data_path}, f)
    print(f"Cache written: {path}")


def main():
    parser = argparse.ArgumentParser(description="Research cache manager")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", metavar="TOPIC", help="Check for a cache hit (exits 0 on hit, 1 on miss)")
    group.add_argument("--write", nargs=2, metavar=("TOPIC", "DATA_PATH"), help="Write a cache entry")
    args = parser.parse_args()

    if args.check:
        hit = check(args.check)
        sys.exit(0 if hit else 1)
    else:
        write(args.write[0], args.write[1])


if __name__ == "__main__":
    main()
