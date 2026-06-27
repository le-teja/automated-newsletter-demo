#!/usr/bin/env python3
"""Archive the current .tmp/output/ run before starting a new newsletter generation."""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", ".tmp", "output")
ARCHIVE_BASE = os.path.join(os.path.dirname(__file__), "..", ".tmp", "archive")
CONTENT_JSON = os.path.join(os.path.dirname(__file__), "..", ".tmp", "newsletter_content.json")


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:40].strip("-")


def find_existing_runs() -> list[dict]:
    if not os.path.exists(ARCHIVE_BASE):
        return []
    runs = []
    for entry in sorted(os.listdir(ARCHIVE_BASE)):
        full = os.path.join(ARCHIVE_BASE, entry)
        if not os.path.isdir(full):
            continue
        meta_path = os.path.join(full, "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
        else:
            meta = {"folder": entry}
        runs.append({"folder": entry, "path": full, "meta": meta})
    return runs


def output_has_content() -> bool:
    if not os.path.exists(OUTPUT_DIR):
        return False
    files = os.listdir(OUTPUT_DIR)
    return any(f.endswith(".html") or f.endswith(".txt") for f in files)


def check_mode():
    """Print current run status and list of archives. Exit 0 if output exists, 1 if empty."""
    runs = find_existing_runs()
    has_output = output_has_content()

    if not has_output:
        print("NO_CURRENT_RUN")
        print("No current output found in .tmp/output/ — nothing to archive.")
    else:
        print("CURRENT_RUN_EXISTS")
        # Detect topic from content JSON if available
        topic = "Unknown"
        if os.path.exists(CONTENT_JSON):
            try:
                with open(CONTENT_JSON, encoding="utf-8") as f:
                    content = json.load(f)
                    subj = content.get("subject_lines", [])
                    if subj:
                        topic = subj[0][:60]
            except Exception:
                pass
        files = os.listdir(OUTPUT_DIR)
        print(f"Current run: {len(files)} file(s) in .tmp/output/")
        print(f"  Detected topic: {topic}")
        for fname in sorted(files):
            fpath = os.path.join(OUTPUT_DIR, fname)
            size = os.path.getsize(fpath)
            print(f"  - {fname} ({size // 1024}KB)")

    if runs:
        print(f"\nExisting archives ({len(runs)}):")
        for r in runs:
            ts = r["meta"].get("archived_at", r["folder"])
            topic = r["meta"].get("topic", "")
            subject = r["meta"].get("subject_line", "")
            label = topic or subject or r["folder"]
            print(f"  [{ts}] {label}")
    else:
        print("\nNo previous archives found.")

    sys.exit(0 if has_output else 1)


def archive_mode(topic: str, subject_line: str = ""):
    """Copy .tmp/output/ into a timestamped archive folder and write metadata."""
    if not output_has_content():
        print("Nothing to archive — .tmp/output/ is empty or missing.")
        sys.exit(0)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    slug = slugify(topic) if topic else "newsletter"
    folder_name = f"{ts}_{slug}"
    dest = os.path.join(ARCHIVE_BASE, folder_name)

    os.makedirs(dest, exist_ok=True)

    copied = []
    for fname in os.listdir(OUTPUT_DIR):
        src = os.path.join(OUTPUT_DIR, fname)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(dest, fname))
            copied.append(fname)

    # Also copy newsletter_content.json if it exists
    if os.path.exists(CONTENT_JSON):
        shutil.copy2(CONTENT_JSON, os.path.join(dest, "newsletter_content.json"))
        copied.append("newsletter_content.json")

    # Write metadata
    meta = {
        "archived_at": ts,
        "topic": topic,
        "subject_line": subject_line,
        "files": copied,
        "folder": folder_name,
    }
    with open(os.path.join(dest, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"Archived {len(copied)} file(s) to .tmp/archive/{folder_name}/")
    for fname in sorted(copied):
        print(f"  - {fname}")


def main():
    parser = argparse.ArgumentParser(description="Archive or inspect newsletter run output")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("check", help="Show current run status and existing archives")

    archive_p = subparsers.add_parser("archive", help="Archive the current .tmp/output/ run")
    archive_p.add_argument("--topic", default="", help="Topic of the newsletter being archived")
    archive_p.add_argument("--subject", default="", help="Subject line chosen for this run")

    args = parser.parse_args()

    if args.command == "check":
        check_mode()
    elif args.command == "archive":
        archive_mode(args.topic, args.subject)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
