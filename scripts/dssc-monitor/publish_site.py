#!/usr/bin/env python3
"""Publish a daily, read-only DSSC snapshot to the Solar Oracle Walkman site."""

import argparse
import csv
import datetime as dt
import fcntl
import hashlib
import io
import json
import math
import os
import random
import statistics
import subprocess
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
SOURCE_CSV = BASE / "readings.csv"
PUBLISH_REPO = Path(
    os.environ.get(
        "DSSC_PUBLISH_REPO",
        "/Users/shihweichieh/.openclaw/workspace/github-automation/solar-oracle-walkman",
    )
)
CONFIG = json.loads((BASE / "channels.json").read_text())
CHANNEL = CONFIG["channels"][0]
DEVICE_NAME = CHANNEL["sample_id"]
SITE_DATA = PUBLISH_REPO / "site" / "data" / DEVICE_NAME
PUBLIC_READINGS = SITE_DATA / "readings.csv"
PUBLIC_DAILY = SITE_DATA / "daily.csv"
PUBLIC_STATUS = SITE_DATA / "status.json"
LOCK_FILE = BASE / ".publish_site.lock"

TAIPEI = dt.timezone(dt.timedelta(hours=8))
BASELINE_DURATION = dt.timedelta(hours=72)
LIGHT_TOLERANCE = 0.10
TEMP_TOLERANCE_C = 2.0
RECENT_DAYS = 7
MIN_COMPLETE_DAY_SAMPLES = 36
MIN_COMPLETE_DAY_HOURS = 6

DAILY_HEADER = [
    "date",
    "valid_samples",
    "condition_matched_samples",
    "condition_matched_hours",
    "comparable_voc_mV",
    "retention_pct",
    "retention_ci_low_pct",
    "retention_ci_high_pct",
    "moving_7d_median_pct",
    "lux_median",
    "ambient_temp_C_median",
    "humidity_pct_median",
    "quality",
]

READINGS_HEADER = [
    "timestamp",
    "raw",
    "voltage_mV",
    "voltage_V",
    "ambient_temp_C",
    "humidity_pct",
    "pressure_hPa",
    "lux",
    "mcu_temp_C",
    "temp_source",
    "light_source",
    "light_condition",
    "quality",
    "quality_reason",
    "device_id",
    "sample_id",
    "gpio",
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--push",
        action="store_true",
        help="Commit and push generated public files after updating them.",
    )
    return parser.parse_args()


def run(command, cwd=PUBLISH_REPO, check=True):
    result = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")
    return result


def git_prepare():
    if not (PUBLISH_REPO / ".git").exists():
        raise RuntimeError(f"Publishing checkout is missing: {PUBLISH_REPO}")
    dirty = run(["git", "status", "--porcelain"]).stdout.strip()
    if dirty:
        raise RuntimeError(
            "Publishing checkout has unexpected local changes; refusing to mix them "
            f"with the daily snapshot:\n{dirty}"
        )
    run(["git", "pull", "--ff-only", "origin", "main"])


def git_publish(now):
    paths = [
        f"site/data/{channel['sample_id']}/{name}"
        for channel in CONFIG["channels"]
        for name in ("readings.csv", "daily.csv", "status.json")
    ] + ["site/data/channels.json"]
    run(["git", "add", "--", *paths])
    changed = run(["git", "diff", "--cached", "--quiet"], check=False)
    if changed.returncode == 0:
        return "no new readings"
    if changed.returncode != 1:
        raise RuntimeError("Unable to inspect staged daily files")
    run(["git", "commit", "-m", f"data: update DSSC snapshot {now:%Y-%m-%d}"])
    pushed = run(["git", "push", "origin", "HEAD:main"], check=False)
    if pushed.returncode:
        run(["git", "pull", "--rebase", "origin", "main"])
        run(["git", "push", "origin", "HEAD:main"])
    return run(["git", "rev-parse", "--short", "HEAD"]).stdout.strip()


def parse_timestamp(value):
    value = (value or "").strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    if len(value) >= 5 and value[-5] in "+-" and value[-3] != ":":
        value = value[:-2] + ":" + value[-2:]
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=TAIPEI)
    return parsed.astimezone(TAIPEI)


def number(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def is_between(value, low, high):
    return value is not None and low <= value <= high


def disconnected_at(when):
    # Date-granularity exclusion is conservative; it is NOT a claimed unplug time.
    since = CHANNEL.get("invalid_from_date")
    if not when or not since or when.astimezone(TAIPEI).date().isoformat() < since:
        return False
    restored = parse_timestamp(CHANNEL.get("confirmed_reconnected_at"))
    return restored is None or when < restored


def select_channel(channel):
    global CHANNEL, DEVICE_NAME, SOURCE_CSV, SITE_DATA, PUBLIC_READINGS, PUBLIC_DAILY, PUBLIC_STATUS
    CHANNEL = channel
    DEVICE_NAME = channel["sample_id"]
    SOURCE_CSV = BASE / channel["source_csv"]
    SITE_DATA = PUBLISH_REPO / "site" / "data" / DEVICE_NAME
    PUBLIC_READINGS = SITE_DATA / "readings.csv"
    PUBLIC_DAILY = SITE_DATA / "daily.csv"
    PUBLIC_STATUS = SITE_DATA / "status.json"


def parse_readings(raw_bytes):
    text = raw_bytes.decode("utf-8-sig")
    parsed = []
    for source in csv.DictReader(io.StringIO(text)):
        when = parse_timestamp(source.get("timestamp"))
        row = {
            "source": source,
            "timestamp": when,
            "voltage_mV": number(source.get("voltage_mV")),
            "voltage_V": number(source.get("voltage_V")),
            "ambient_temp_C": number(source.get("ambient_temp_C")),
            "humidity_pct": number(source.get("humidity_pct")),
            "pressure_hPa": number(source.get("pressure_hPa")),
            "lux": number(source.get("lux")),
            "mcu_temp_C": number(source.get("mcu_temp_C")),
        }
        row["voltage_valid"] = when is not None and is_between(row["voltage_mV"], 0, 1200)
        row["valid"] = bool(
            row["voltage_valid"]
            and is_between(row["ambient_temp_C"], -20, 80)
            and is_between(row["humidity_pct"], 0, 100)
            and is_between(row["pressure_hPa"], 800, 1100)
            and is_between(row["lux"], 0, 200000)
            and is_between(row["mcu_temp_C"], -20, 110)
        )
        row["quality_reason"] = "included" if row["valid"] else "invalid_sensor_range_or_missing"
        if disconnected_at(when):
            row["valid"] = False
            row["voltage_valid"] = False
            row["quality_reason"] = "sensor_disconnected_invalid_measurement"
        parsed.append(row)
    return sorted((row for row in parsed if row["timestamp"]), key=lambda row: row["timestamp"])


def read_source():
    if not SOURCE_CSV.exists():
        if CHANNEL["gpio"] == 2:
            return b"", []  # Never invent B history before actual acquisition.
        raise RuntimeError(f"Readings file is missing: {SOURCE_CSV}")
    with SOURCE_CSV.open("rb") as source:
        fcntl.flock(source.fileno(), fcntl.LOCK_SH)
        raw_bytes = source.read()
        fcntl.flock(source.fileno(), fcntl.LOCK_UN)
    return raw_bytes, parse_readings(raw_bytes)


def median(values):
    values = [value for value in values if value is not None]
    return statistics.median(values) if values else None


def condition_matches(row, reference_lux, reference_temp):
    if not row["valid"] or reference_lux is None or reference_temp is None:
        return False
    return (
        reference_lux * (1 - LIGHT_TOLERANCE)
        <= row["lux"]
        <= reference_lux * (1 + LIGHT_TOLERANCE)
        and abs(row["ambient_temp_C"] - reference_temp) <= TEMP_TOLERANCE_C
    )


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def bootstrap_median_ci(values, seed):
    if len(values) < 3:
        return None, None
    rng = random.Random(seed)
    simulations = []
    for _ in range(1000):
        simulations.append(statistics.median(rng.choices(values, k=len(values))))
    return percentile(simulations, 0.025), percentile(simulations, 0.975)


def derive_daily(rows, now):
    valid_rows = [row for row in rows if row["valid"]]
    baseline_start = valid_rows[0]["timestamp"] if valid_rows else now
    baseline_end = baseline_start + BASELINE_DURATION
    baseline_rows = [row for row in valid_rows if row["timestamp"] < baseline_end]
    reference_lux = median(row["lux"] for row in baseline_rows)
    reference_temp = median(row["ambient_temp_C"] for row in baseline_rows)
    baseline_matched = [
        row for row in baseline_rows if condition_matches(row, reference_lux, reference_temp)
    ]
    reference_voc = median(row["voltage_mV"] for row in baseline_matched)
    if reference_voc is None:
        reference_voc = median(row["voltage_mV"] for row in baseline_rows)

    dates = sorted({row["timestamp"].date() for row in rows})
    daily = []
    qualified_retention = []
    for day in dates:
        day_rows = [row for row in valid_rows if row["timestamp"].date() == day]
        matched = [
            row for row in day_rows if condition_matches(row, reference_lux, reference_temp)
        ]
        hourly = {}
        for row in matched:
            key = row["timestamp"].replace(minute=0, second=0, microsecond=0)
            hourly.setdefault(key, []).append(row["voltage_mV"])
        hourly_medians = [statistics.median(values) for values in hourly.values()]
        comparable_voc = median(hourly_medians)
        retention = (
            100.0 * comparable_voc / reference_voc
            if comparable_voc is not None and reference_voc
            else None
        )
        ci_low_voc, ci_high_voc = bootstrap_median_ci(
            hourly_medians, int(day.strftime("%Y%m%d"))
        )
        complete = bool(
            day < now.date()
            and len(matched) >= MIN_COMPLETE_DAY_SAMPLES
            and len(hourly) >= MIN_COMPLETE_DAY_HOURS
            and now >= baseline_end
        )
        if complete and retention is not None:
            qualified_retention.append(retention)
        moving = median(qualified_retention[-7:]) if day_rows and len(qualified_retention) >= 3 else None
        daily.append(
            {
                "date": day.isoformat(),
                "valid_samples": len(day_rows),
                "condition_matched_samples": len(matched),
                "condition_matched_hours": len(hourly),
                "comparable_voc_mV": comparable_voc,
                "retention_pct": retention,
                "retention_ci_low_pct": (
                    100.0 * ci_low_voc / reference_voc
                    if ci_low_voc is not None and reference_voc
                    else None
                ),
                "retention_ci_high_pct": (
                    100.0 * ci_high_voc / reference_voc
                    if ci_high_voc is not None and reference_voc
                    else None
                ),
                "moving_7d_median_pct": moving,
                "lux_median": median(row["lux"] for row in day_rows),
                "ambient_temp_C_median": median(row["ambient_temp_C"] for row in day_rows),
                "humidity_pct_median": median(row["humidity_pct"] for row in day_rows),
                "quality": ("complete" if complete else "partial") if day_rows else "invalid_measurement",
            }
        )

    complete_points = [row for row in daily if row["quality"] == "complete"]
    slope = None
    if len(complete_points) >= 7:
        slopes = []
        for index, left in enumerate(complete_points):
            left_day = dt.date.fromisoformat(left["date"])
            for right in complete_points[index + 1 :]:
                right_day = dt.date.fromisoformat(right["date"])
                elapsed = (right_day - left_day).days
                if elapsed:
                    slopes.append(
                        (right["retention_pct"] - left["retention_pct"]) / elapsed
                    )
        slope = median(slopes)

    baseline = {
        "start": baseline_start.isoformat(),
        "end": baseline_end.isoformat(),
        "state": "fixed" if now >= baseline_end else "collecting",
        "valid_samples": len(baseline_rows),
        "matched_samples": len(baseline_matched),
        "reference_lux": reference_lux,
        "reference_temp_C": reference_temp,
        "reference_voc_mV": reference_voc,
        "light_tolerance_pct": LIGHT_TOLERANCE * 100,
        "temperature_tolerance_C": TEMP_TOLERANCE_C,
    }
    return daily, baseline, slope


def rounded(value, digits=2):
    return round(value, digits) if value is not None else None


def json_reading(row):
    return {
        "timestamp": row["timestamp"].isoformat(timespec="seconds"),
        "voltage_mV": rounded(row["voltage_mV"], 1),
        "ambient_temp_C": rounded(row["ambient_temp_C"], 2),
        "humidity_pct": rounded(row["humidity_pct"], 2),
        "pressure_hPa": rounded(row["pressure_hPa"], 2),
        "lux": rounded(row["lux"], 1),
        "mcu_temp_C": rounded(row["mcu_temp_C"], 1),
        "valid": row["valid"],
        "quality_reason": row["quality_reason"],
        "sample_id": DEVICE_NAME,
        "device_id": CONFIG["device_id"],
        "gpio": CHANNEL["gpio"],
    }


def serialize_daily_csv(daily):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=DAILY_HEADER, lineterminator="\n")
    writer.writeheader()
    for row in daily:
        writer.writerow(
            {
                key: (
                    f"{value:.3f}"
                    if isinstance(value, float)
                    else value
                )
                for key, value in row.items()
            }
        )
    return buffer.getvalue().encode("utf-8")


def serialize_public_readings(rows):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=READINGS_HEADER, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        source = row["source"]
        writer.writerow(
            {
                "timestamp": row["timestamp"].isoformat(timespec="seconds"),
                "raw": source.get("raw", ""),
                "voltage_mV": source.get("voltage_mV", ""),
                "voltage_V": source.get("voltage_V", ""),
                "ambient_temp_C": source.get("ambient_temp_C", ""),
                "humidity_pct": source.get("humidity_pct", ""),
                "pressure_hPa": source.get("pressure_hPa", ""),
                "lux": source.get("lux", ""),
                "mcu_temp_C": source.get("mcu_temp_C", ""),
                "temp_source": source.get("temp_source", ""),
                "light_source": source.get("light_source", ""),
                "light_condition": source.get("light_condition", ""),
                "quality": "included" if row["valid"] else "excluded",
                "quality_reason": row["quality_reason"],
                "device_id": CONFIG["device_id"],
                "sample_id": DEVICE_NAME,
                "gpio": CHANNEL["gpio"],
            }
        )
    return buffer.getvalue().encode("utf-8")


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    mode = "wb" if isinstance(content, bytes) else "w"
    kwargs = {} if isinstance(content, bytes) else {"encoding": "utf-8"}
    with temporary.open(mode, **kwargs) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def build_snapshot(raw_bytes, rows, now):
    daily, baseline, slope = derive_daily(rows, now)
    valid_rows = [row for row in rows if row["valid"]]
    latest = rows[-1] if rows else None
    recent_start = now - dt.timedelta(days=RECENT_DAYS)
    recent = [row for row in rows if row["timestamp"] >= recent_start]
    latest_age_minutes = (
        (now - latest["timestamp"]).total_seconds() / 60 if latest else None
    )
    status = {
        "device": DEVICE_NAME,  # Legacy field preserved; device_id is physical board.
        "schema_version": 2,
        "device_id": CONFIG["device_id"],
        "sample_id": DEVICE_NAME,
        "display_name": CHANNEL["display_name"],
        "gpio": CHANNEL["gpio"],
        "connection_state": "unknown/disconnected" if disconnected_at(now) else CHANNEL["connection_state"],
        "quality_policy": CHANNEL,
        "first_observed_at": rows[0]["timestamp"].isoformat() if rows else None,
        "first_valid_at": valid_rows[0]["timestamp"].isoformat() if valid_rows else None,
        "generated_at": now.isoformat(timespec="seconds"),
        "snapshot_state": "unknown/disconnected" if disconnected_at(now) else (
            "continuous"
            if latest and latest["valid"] and latest_age_minutes is not None and latest_age_minutes <= 15
            else "interrupted"
        ),
        "latest_age_minutes": rounded(latest_age_minutes, 1),
        "sample_count": len(rows),
        "valid_sample_count": len(valid_rows),
        "invalid_sample_count": len(rows) - len(valid_rows),
        "latest": json_reading(latest) if latest else None,
        "baseline": {key: rounded(value, 2) if isinstance(value, float) else value for key, value in baseline.items()},
        "complete_comparable_days": sum(row["quality"] == "complete" for row in daily),
        "trend_state": (
            "estimated" if slope is not None else "collecting_comparable_days"
        ),
        "theil_sen_slope_pct_per_day": rounded(slope, 4),
        "daily": [
            {
                key: rounded(value, 3) if isinstance(value, float) else value
                for key, value in row.items()
            }
            for row in daily
        ],
        "recent": [json_reading(row) for row in recent],
        "raw_csv_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    }
    atomic_write(PUBLIC_READINGS, serialize_public_readings(rows))
    atomic_write(PUBLIC_DAILY, serialize_daily_csv(daily))
    atomic_write(
        PUBLIC_STATUS,
        json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return status


def main():
    args = parse_args()
    LOCK_FILE.touch(exist_ok=True)
    with LOCK_FILE.open("r+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another site snapshot is still running")
        if args.push:
            git_prepare()
        now = dt.datetime.now(TAIPEI)
        for channel in CONFIG["channels"]:
            select_channel(channel)
            raw_bytes, rows = read_source()
            status = build_snapshot(raw_bytes, rows, now)
            print(f"{channel['display_name']}: {len(rows)} raw / {status['valid_sample_count']} valid; {status['snapshot_state']}")
        atomic_write(PUBLISH_REPO / "site/data/channels.json", json.dumps(CONFIG, ensure_ascii=False, indent=2) + "\n")
        revision = git_publish(now) if args.push else "prepared locally"
        print(f"publication {revision}")



if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"publish failed: {error}", file=sys.stderr)
        raise SystemExit(1)
