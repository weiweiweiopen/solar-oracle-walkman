#!/usr/bin/env python3
import json
import sys
from pathlib import Path

EVENTS_FILE = Path("data/registry/events.example.jsonl")
REQUIRED_FIELDS = {
    "event_id",
    "device_id",
    "timestamp",
    "measurement_type",
    "challenge",
    "features",
    "raw_data_hash",
    "oracle_signature_status",
    "chain_anchor",
    "status",
    "not_claimed_as",
}
REQUIRED_FEATURES = {
    "FF",
    "Vmpp_over_Voc",
    "Impp_over_Isc",
    "Rs_star",
    "Rsh_star",
    "curvature_sum",
    "area_star",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def main() -> None:
    if not EVENTS_FILE.exists():
        fail(f"Missing file: {EVENTS_FILE}")

    content = EVENTS_FILE.read_text(encoding="utf-8").splitlines()
    if not content:
        fail("events.example.jsonl is empty")

    for idx, line in enumerate(content, start=1):
        if not line.strip():
            fail(f"Line {idx} is empty")

        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"Line {idx} invalid JSON: {exc}")

        missing_fields = sorted(REQUIRED_FIELDS - set(event.keys()))
        if missing_fields:
            fail(f"Line {idx} missing required fields: {', '.join(missing_fields)}")

        features = event.get("features")
        if not isinstance(features, dict):
            fail(f"Line {idx} features must be an object")

        missing_features = sorted(REQUIRED_FEATURES - set(features.keys()))
        if missing_features:
            fail(f"Line {idx} missing required features: {', '.join(missing_features)}")

    print(f"Schema validation passed for {EVENTS_FILE} ({len(content)} event line(s)).")


if __name__ == "__main__":
    main()
