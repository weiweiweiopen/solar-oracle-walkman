#!/usr/bin/env python3
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

EVENTS_FILE = Path("data/registry/events.example.jsonl")
HASHES_FILE = Path("data/registry/daily_hashes.example.json")


def compute_sha256(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def update_hash_registry(sha256_hex: str) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payload = {
        "note": "Example hash registry. Entries are generated from example event data.",
        "entries": [
            {
                "date": now[:10],
                "source_file": str(EVENTS_FILE),
                "sha256": sha256_hex,
                "status": "example_only",
                "not_claimed_as": [
                    "blockchain_anchored",
                    "legal_REC",
                    "T-REC",
                    "financial_product"
                ],
                "generated_at": now
            }
        ]
    }
    HASHES_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate daily SHA-256 hash for example event registry.")
    parser.add_argument("--update", action="store_true", help="Update data/registry/daily_hashes.example.json")
    args = parser.parse_args()

    if not EVENTS_FILE.exists():
        raise SystemExit(f"ERROR: Missing file: {EVENTS_FILE}")

    sha256_hex = compute_sha256(EVENTS_FILE)
    print(f"SHA-256 ({EVENTS_FILE}): {sha256_hex}")

    if args.update:
        update_hash_registry(sha256_hex)
        print(f"Updated {HASHES_FILE}")


if __name__ == "__main__":
    main()
