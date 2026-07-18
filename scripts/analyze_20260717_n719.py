#!/usr/bin/env python3
"""Analyze 2026-07-17 N719 LSV records and compare A–E with 2026-07-13.

Inclusion rules from the measurement note:
- Include boards A–K.
- Exclude the separately labelled 6x6 board.
- Compare A–E with their 2026-07-13 enrollment records.
- Treat F–K as first-measurement baselines; do not make cross-date identity claims.
"""
from __future__ import annotations

import csv
import json
import math
import re
import shutil
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
CURRENT_DATE = "2026-07-17"
REFERENCE_DATE = "2026-07-13"
CURRENT_GROUPS = list("abcdefghijk")
REFERENCE_GROUPS = list("abcde")
FIRST_MEASUREMENT_GROUPS = list("fghijk")

DATA_DIR = ROOT / "data/lab/2026-07-17-n719"
RAW_DIR = DATA_DIR / "raw/ec-lab-txt"
REFERENCE_RAW_DIR = ROOT / "data/lab/2026-07-13-n719/raw/ec-lab-txt"
PROCESSED_DIR = DATA_DIR / "processed"
FIG_DIR = DATA_DIR / "figures"
SITE_DATA_DIR = ROOT / "site/data"
SITE_FIG_DIR = ROOT / "site/pix/rmse"

for directory in [PROCESSED_DIR, FIG_DIR, SITE_DATA_DIR, SITE_FIG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

METRIC_LABELS = {
    "raw": "raw current",
    "maxabs": "max-abs normalized",
    "zshape": "z-score shape",
}


def group_sample(path: Path, date_code: str, allowed_groups: list[str]) -> tuple[str, str]:
    allowed = "".join(allowed_groups)
    match = re.search(rf"N719_{date_code}-([{allowed}])-([0-9]+)_C06\.txt$", path.name)
    if not match:
        raise ValueError(f"Unexpected EC-Lab filename: {path.name}")
    return match.group(1), f"{match.group(1)}-{match.group(2)}"


def read_ec_lab_txt(path: Path) -> tuple[np.ndarray, np.ndarray]:
    lines = path.read_text(errors="ignore").splitlines()
    header_lines = 0
    for line in lines[:120]:
        match = re.search(r"Nb header lines\s*:\s*(\d+)", line)
        if match:
            header_lines = int(match.group(1))
            break
    if not header_lines:
        raise ValueError(f"Cannot find EC-Lab header length in {path}")

    header = lines[header_lines - 1].split("\t")
    lowered = [item.lower() for item in header]
    voltage_index = next((i for i, item in enumerate(lowered) if "ewe" in item and "/v" in item), None)
    if voltage_index is None:
        voltage_index = next(i for i, item in enumerate(lowered) if "ewe" in item)
    current_index = next((i for i, item in enumerate(lowered) if "<i>" in item or "i/" in item), None)
    if current_index is None:
        raise ValueError(f"Cannot find current column in {path}")

    voltage: list[float] = []
    current: list[float] = []
    for line in lines[header_lines:]:
        parts = line.split("\t")
        if len(parts) <= max(voltage_index, current_index):
            continue
        try:
            e_value = float(parts[voltage_index].replace(",", "."))
            i_value = float(parts[current_index].replace(",", "."))
        except ValueError:
            continue
        # EC-Lab exports an initial zero-current stabilization segment.
        if abs(i_value) > 1e-12:
            voltage.append(e_value)
            current.append(i_value)

    pairs = sorted(zip(voltage, current))
    if not pairs:
        raise ValueError(f"No active LSV rows found in {path}")
    return np.array([pair[0] for pair in pairs]), np.array([pair[1] for pair in pairs])


def interp_at(voltage: np.ndarray, current: np.ndarray, target: float) -> float:
    if target < voltage.min() or target > voltage.max():
        return math.nan
    return float(np.interp(target, voltage, current))


def zero_cross(voltage: np.ndarray, current: np.ndarray) -> float:
    for e0, i0, e1, i1 in zip(voltage[:-1], current[:-1], voltage[1:], current[1:]):
        if i0 == 0:
            return float(e0)
        if i0 * i1 < 0:
            return float(e0 - i0 * (e1 - e0) / (i1 - i0))
    return math.nan


def rmse(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.sqrt(np.mean((first - second) ** 2)))


def maxabs_normalize(values: np.ndarray) -> np.ndarray:
    maximum = np.max(np.abs(values))
    return values / maximum if maximum else values * 0


def zscore_normalize(values: np.ndarray) -> np.ndarray:
    deviation = np.std(values)
    return (values - np.mean(values)) / deviation if deviation else values * 0


def json_number(value: float | int) -> float | int | None:
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def csv_number(value: float | int) -> float | int | str:
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return ""
    return value


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"Cannot write empty CSV: {path}")
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_curves(directory: Path, date_code: str, date: str, groups: list[str]) -> list[dict]:
    curves: list[dict] = []
    for expected_group in groups:
        for path in sorted(directory.glob(f"N719_{date_code}-{expected_group}-*_C06.txt")):
            group, sample = group_sample(path, date_code, groups)
            voltage, current = read_ec_lab_txt(path)
            curves.append(
                {
                    "date": date,
                    "group": group,
                    "sample": sample,
                    "file": path.name,
                    "E": voltage,
                    "I": current,
                }
            )
    return curves


current_curves = load_curves(RAW_DIR, "0717", CURRENT_DATE, CURRENT_GROUPS)
reference_curves = load_curves(REFERENCE_RAW_DIR, "0713", REFERENCE_DATE, REFERENCE_GROUPS)

if not current_curves:
    raise SystemExit("No 2026-07-17 A–K EC-Lab text files found.")
if any("6x6" in curve["file"].lower() for curve in current_curves):
    raise SystemExit("The excluded 6x6 board entered the analysis unexpectedly.")

current_counts = {group: sum(curve["group"] == group for curve in current_curves) for group in CURRENT_GROUPS}
reference_counts = {group: sum(curve["group"] == group for curve in reference_curves) for group in REFERENCE_GROUPS}
if any(count != 2 for count in current_counts.values()):
    raise SystemExit(f"Expected two 2026-07-17 scans per A–K board; got {current_counts}")
if any(count < 2 for count in reference_counts.values()):
    raise SystemExit(f"Reference enrollment is incomplete: {reference_counts}")

all_curves = reference_curves + current_curves
common_low = max(float(curve["E"].min()) for curve in all_curves)
common_high = min(float(curve["E"].max()) for curve in all_curves)
grid = np.linspace(common_low, common_high, 800)

for curve in all_curves:
    raw = np.interp(grid, curve["E"], curve["I"])
    curve["raw"] = raw
    curve["maxabs"] = maxabs_normalize(raw)
    curve["zshape"] = zscore_normalize(raw)

# Per-scan and per-group summaries for the new A–K records.
scan_rows: list[dict] = []
for curve in current_curves:
    voltage = curve["E"]
    current = curve["I"]
    scan_rows.append(
        {
            "date": CURRENT_DATE,
            "group": curve["group"],
            "sample": curve["sample"],
            "file": curve["file"],
            "points_active": len(voltage),
            "E_min_V_vs_SCE": float(voltage.min()),
            "E_max_V_vs_SCE": float(voltage.max()),
            "I_min_mA": float(current.min()),
            "I_max_mA": float(current.max()),
            "I_at_-0.6V_mA": interp_at(voltage, current, -0.6),
            "I_at_-0.4V_mA": interp_at(voltage, current, -0.4),
            "I_at_-0.2V_mA": interp_at(voltage, current, -0.2),
            "I_at_0V_mA": interp_at(voltage, current, 0.0),
            "zero_cross_E_V_vs_SCE": zero_cross(voltage, current),
        }
    )
write_csv(PROCESSED_DIR / "scan_metrics.csv", [{key: csv_number(value) for key, value in row.items()} for row in scan_rows])

group_rows: list[dict] = []
for group in CURRENT_GROUPS:
    rows = [row for row in scan_rows if row["group"] == group]
    output: dict = {"date": CURRENT_DATE, "group": group, "n_scans": len(rows)}
    for field in [
        "I_min_mA",
        "I_max_mA",
        "I_at_-0.6V_mA",
        "I_at_-0.4V_mA",
        "I_at_-0.2V_mA",
        "I_at_0V_mA",
        "zero_cross_E_V_vs_SCE",
    ]:
        values = [row[field] for row in rows if not math.isnan(row[field])]
        output[field + "_mean"] = statistics.mean(values) if values else math.nan
        output[field + "_sd"] = statistics.stdev(values) if len(values) > 1 else 0.0 if values else math.nan
    group_rows.append(output)
write_csv(PROCESSED_DIR / "group_summary.csv", [{key: csv_number(value) for key, value in row.items()} for row in group_rows])

# Within-session repeatability and A–K separability.
pairwise_by_kind: dict[str, list[dict]] = {}
within_summary_rows: list[dict] = []
for kind in ["raw", "maxabs", "zshape"]:
    pairs: list[dict] = []
    for index, first in enumerate(current_curves):
        for second in current_curves[index + 1 :]:
            pairs.append(
                {
                    "kind": kind,
                    "same_group": first["group"] == second["group"],
                    "group_pair": f"{first['group']}-{second['group']}",
                    "file_a": first["file"],
                    "file_b": second["file"],
                    "rmse": rmse(first[kind], second[kind]),
                }
            )
    pairwise_by_kind[kind] = pairs
    write_csv(PROCESSED_DIR / f"{kind}_rmse_pairwise.csv", pairs)
    within = [pair["rmse"] for pair in pairs if pair["same_group"]]
    between = [pair["rmse"] for pair in pairs if not pair["same_group"]]
    within_summary_rows.append(
        {
            "kind": kind,
            "intra_mean": statistics.mean(within),
            "intra_max": max(within),
            "inter_mean": statistics.mean(between),
            "inter_min": min(between),
            "inter_min_over_intra_max": min(between) / max(within),
        }
    )
write_csv(PROCESSED_DIR / "rmse_summary.csv", within_summary_rows)

current_means: dict[tuple[str, str], np.ndarray] = {}
reference_means: dict[tuple[str, str], np.ndarray] = {}
current_mean_rows: list[dict] = []
for kind in ["raw", "maxabs", "zshape"]:
    for group in CURRENT_GROUPS:
        current_means[(kind, group)] = np.mean(
            [curve[kind] for curve in current_curves if curve["group"] == group], axis=0
        )
    for group in REFERENCE_GROUPS:
        reference_means[(kind, group)] = np.mean(
            [curve[kind] for curve in reference_curves if curve["group"] == group], axis=0
        )
    for index, first_group in enumerate(CURRENT_GROUPS):
        for second_group in CURRENT_GROUPS[index + 1 :]:
            current_mean_rows.append(
                {
                    "kind": kind,
                    "group_pair": f"{first_group}-{second_group}",
                    "rmse": rmse(current_means[(kind, first_group)], current_means[(kind, second_group)]),
                }
            )
write_csv(PROCESSED_DIR / "group_mean_rmse.csv", current_mean_rows)

# Provisional per-group acceptance bands from 2026-07-13 leave-one-out enrollment variation.
# These are lower-bound pilot bands, not validated long-term thresholds.
reference_loo_rows: list[dict] = []
reference_loo_max: dict[tuple[str, str], float] = {}
for kind in ["raw", "maxabs", "zshape"]:
    for group in REFERENCE_GROUPS:
        distances: list[float] = []
        group_curves = [curve for curve in reference_curves if curve["group"] == group]
        for curve in group_curves:
            others = [item[kind] for item in group_curves if item["file"] != curve["file"]]
            template = np.mean(others, axis=0)
            distance = rmse(curve[kind], template)
            distances.append(distance)
            reference_loo_rows.append(
                {
                    "kind": kind,
                    "group": group,
                    "left_out_file": curve["file"],
                    "leave_one_out_same_label_rmse": distance,
                }
            )
        reference_loo_max[(kind, group)] = max(distances)
write_csv(PROCESSED_DIR / "reference_leave_one_out.csv", reference_loo_rows)

# Cross-date A–E distance matrices and transparent nearest-template decisions.
cross_distance_rows: dict[str, list[dict]] = {}
metric_details: dict[str, dict[str, dict]] = {group: {} for group in REFERENCE_GROUPS}
for kind in ["raw", "maxabs", "zshape"]:
    rows: list[dict] = []
    for query_group in REFERENCE_GROUPS:
        for reference_group in REFERENCE_GROUPS:
            rows.append(
                {
                    "kind": kind,
                    "query_date": CURRENT_DATE,
                    "query_group": query_group,
                    "reference_date": REFERENCE_DATE,
                    "reference_group": reference_group,
                    "same_label": query_group == reference_group,
                    "rmse": rmse(
                        current_means[(kind, query_group)],
                        reference_means[(kind, reference_group)],
                    ),
                }
            )
    cross_distance_rows[kind] = rows
    write_csv(PROCESSED_DIR / f"cross_date_{kind}_distance_matrix.csv", rows)

    for group in REFERENCE_GROUPS:
        group_distances = sorted(
            (row["rmse"], row["reference_group"])
            for row in rows
            if row["query_group"] == group
        )
        correct_distance = next(distance for distance, label in group_distances if label == group)
        nearest_wrong_distance, nearest_wrong_label = next(
            (distance, label) for distance, label in group_distances if label != group
        )
        scan_predictions: list[dict] = []
        for curve in current_curves:
            if curve["group"] != group:
                continue
            scan_distances = sorted(
                (rmse(curve[kind], reference_means[(kind, reference_group)]), reference_group)
                for reference_group in REFERENCE_GROUPS
            )
            scan_predictions.append(
                {
                    "sample": curve["sample"],
                    "prediction": scan_distances[0][1],
                    "rmse": scan_distances[0][0],
                }
            )
        nearest_distance, nearest_label = group_distances[0]
        mean_matches = nearest_label == group
        scans_match = all(item["prediction"] == group for item in scan_predictions)
        nearest_label_consistent = mean_matches and scans_match
        acceptance_band = reference_loo_max[(kind, group)]
        within_reference_band = correct_distance <= acceptance_band
        metric_details[group][kind] = {
            "nearestReference": nearest_label,
            "nearestRmse": nearest_distance,
            "sameLabelRmse": correct_distance,
            "nearestWrongReference": nearest_wrong_label,
            "nearestWrongRmse": nearest_wrong_distance,
            "wrongOverCorrectMargin": nearest_wrong_distance / correct_distance if correct_distance else None,
            "meanMatches": mean_matches,
            "allScansMatch": scans_match,
            "nearestLabelConsistent": nearest_label_consistent,
            "referenceLeaveOneOutMaxRmse": acceptance_band,
            "sameLabelOverReferenceBand": correct_distance / acceptance_band if acceptance_band else None,
            "withinReferenceBand": within_reference_band,
            "passes": nearest_label_consistent and within_reference_band,
            "scanPredictions": scan_predictions,
        }

identification_rows: list[dict] = []
identification_json: list[dict] = []
for group in REFERENCE_GROUPS:
    normalized_passes = [
        kind for kind in ["maxabs", "zshape"] if metric_details[group][kind]["passes"]
    ]
    raw_passes = metric_details[group]["raw"]["passes"]
    normalized_nearest_views = [
        kind
        for kind in ["maxabs", "zshape"]
        if metric_details[group][kind]["nearestLabelConsistent"]
    ]
    raw_nearest_consistent = metric_details[group]["raw"]["nearestLabelConsistent"]
    nearest_label_views = (["raw"] if raw_nearest_consistent else []) + normalized_nearest_views
    scan_disagreement = any(
        len({item["prediction"] for item in metric_details[group][kind]["scanPredictions"]}) > 1
        for kind in ["raw", "maxabs", "zshape"]
    )

    if len(normalized_passes) == 2:
        result = "recognizable"
        status = "Recognizable against 2026-07-13 references in both normalized views and within the enrollment band."
    else:
        result = "not_recognizable"
        if normalized_nearest_views:
            labels = ", ".join(METRIC_LABELS[kind] for kind in normalized_nearest_views)
            status = f"Not re-identified — only {labels} chose the expected label, and the distance exceeded enrollment variation."
        elif raw_nearest_consistent:
            status = "Not re-identified by normalized shape — raw current chose the expected label, but its distance exceeded enrollment variation."
        else:
            status = "Not re-identified against the 2026-07-13 references."
    if scan_disagreement:
        status += " Repeat scans also disagree."

    reference_i0 = next(
        row["I_at_0V_mA_mean"]
        for row in csv.DictReader((ROOT / "data/lab/2026-07-13-n719/processed/group_summary.csv").open())
        if row["group"] == group
    )
    reference_i0_value = float(reference_i0)
    current_i0_value = next(row["I_at_0V_mA_mean"] for row in group_rows if row["group"] == group)
    i0_change_percent = (
        (current_i0_value - reference_i0_value) / abs(reference_i0_value) * 100
        if reference_i0_value
        else math.nan
    )

    flat_row: dict = {
        "group": group,
        "reference_date": REFERENCE_DATE,
        "query_date": CURRENT_DATE,
        "n_reference": reference_counts[group],
        "n_query": current_counts[group],
        "reference_I_at_0V_mA": reference_i0_value,
        "query_I_at_0V_mA": current_i0_value,
        "I_at_0V_change_percent": i0_change_percent,
    }
    for kind in ["raw", "maxabs", "zshape"]:
        detail = metric_details[group][kind]
        flat_row.update(
            {
                f"{kind}_nearest_reference": detail["nearestReference"],
                f"{kind}_same_label_rmse": detail["sameLabelRmse"],
                f"{kind}_nearest_rmse": detail["nearestRmse"],
                f"{kind}_nearest_wrong_reference": detail["nearestWrongReference"],
                f"{kind}_nearest_wrong_rmse": detail["nearestWrongRmse"],
                f"{kind}_wrong_over_correct_margin": detail["wrongOverCorrectMargin"],
                f"{kind}_mean_matches": detail["meanMatches"],
                f"{kind}_all_scans_match": detail["allScansMatch"],
                f"{kind}_nearest_label_consistent": detail["nearestLabelConsistent"],
                f"{kind}_reference_leave_one_out_max_rmse": detail["referenceLeaveOneOutMaxRmse"],
                f"{kind}_same_label_over_reference_band": detail["sameLabelOverReferenceBand"],
                f"{kind}_within_reference_band": detail["withinReferenceBand"],
                f"{kind}_passes": detail["passes"],
            }
        )
    flat_row.update(
        {
            "nearest_label_views": "+".join(nearest_label_views) if nearest_label_views else "none",
            "normalized_views_passed": "+".join(normalized_passes) if normalized_passes else "none",
            "raw_view_passed": raw_passes,
            "repeat_scan_prediction_disagreement": scan_disagreement,
            "result": result,
            "interpretation": status,
        }
    )
    identification_rows.append(flat_row)
    identification_json.append(
        {
            "group": group,
            "result": result,
            "status": status,
            "nearestLabelViews": nearest_label_views,
            "normalizedViewsPassed": normalized_passes,
            "rawViewPassed": raw_passes,
            "repeatScanPredictionDisagreement": scan_disagreement,
            "referenceIAt0VmA": reference_i0_value,
            "queryIAt0VmA": current_i0_value,
            "iAt0VChangePercent": i0_change_percent,
            "metrics": metric_details[group],
        }
    )
write_csv(PROCESSED_DIR / "cross_date_identification.csv", identification_rows)

# Compact JSON for the public site and machine-readable result review.
site_groups: list[dict] = []
for group in CURRENT_GROUPS:
    group_curves = [curve for curve in current_curves if curve["group"] == group]
    raw_matrix = np.vstack([curve["raw"] for curve in group_curves])
    raw_mean = raw_matrix.mean(axis=0)
    raw_sd = raw_matrix.std(axis=0, ddof=1)
    zshape_repeat_rmse = rmse(group_curves[0]["zshape"], group_curves[1]["zshape"])
    indexes = np.linspace(0, len(grid) - 1, 160).astype(int)
    summary = next(row for row in group_rows if row["group"] == group)
    comparison = next((item for item in identification_json if item["group"] == group), None)
    status = (
        comparison["status"]
        if comparison
        else "First measurement on 2026-07-17; no cross-date identity decision yet."
    )
    site_groups.append(
        {
            "id": group,
            "title": f"N719 group {group}",
            "date": CURRENT_DATE,
            "replicates": len(group_curves),
            "status": status,
            "comparisonResult": comparison["result"] if comparison else "first_measurement",
            "points": [
                [round(float(grid[index]), 6), round(float(raw_mean[index]), 6)]
                for index in indexes
            ],
            "sdPoints": [
                [round(float(grid[index]), 6), round(float(raw_sd[index]), 6)]
                for index in indexes
            ],
            "metrics": {
                "displayMode": "lsv",
                "n_scans": len(group_curves),
                "I_at_0V_mA_mean": json_number(summary["I_at_0V_mA_mean"]),
                "I_at_0V_mA_sd": json_number(summary["I_at_0V_mA_sd"]),
                "zero_cross_E_V_vs_SCE_mean": json_number(summary["zero_cross_E_V_vs_SCE_mean"]),
                "zero_cross_E_V_vs_SCE_sd": json_number(summary["zero_cross_E_V_vs_SCE_sd"]),
                "duplicate_zshape_rmse": zshape_repeat_rmse,
            },
        }
    )

site_payload = {
    "dataset": "N719_20260717_a-k",
    "date": CURRENT_DATE,
    "xLabel": "Ewe (V vs SCE)",
    "yLabel": "Current <I> (mA)",
    "commonGrid_V_vs_SCE": [round(common_low, 6), round(common_high, 6)],
    "includedGroups": CURRENT_GROUPS,
    "excludedGroups": ["6x6"],
    "exclusionNote": "The separately labelled 6x6 board was excluded by instruction and is not committed to this dataset.",
    "crossDateReference": {
        "date": REFERENCE_DATE,
        "groups": REFERENCE_GROUPS,
        "criterion": (
            "A board is called recognizable only when both amplitude-normalized views "
            "(max-abs and z-score) select its own 2026-07-13 template for the group mean "
            "and both 2026-07-17 repeat scans, and the same-label distance stays within "
            "the provisional 2026-07-13 leave-one-out enrollment band. Raw-current RMSE is supplemental."
        ),
        "resultSummary": "No A–E board passes both normalized cross-date views in this exploratory two-repeat test.",
    },
    "firstMeasurementGroups": FIRST_MEASUREMENT_GROUPS,
    "groups": site_groups,
    "crossDateIdentification": identification_json,
    "withinSessionRmseSummary": within_summary_rows,
}

for output_path in [
    PROCESSED_DIR / "iv_analysis_20260717.json",
    SITE_DATA_DIR / "iv-analysis-20260717.json",
]:
    output_path.write_text(json.dumps(site_payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n")

# Figures.
plt.style.use("seaborn-v0_8-whitegrid")
colors = dict(zip(CURRENT_GROUPS, plt.cm.tab20(np.linspace(0, 1, len(CURRENT_GROUPS)))))

fig, axis = plt.subplots(figsize=(12, 7))
for group in CURRENT_GROUPS:
    group_curves = [curve for curve in current_curves if curve["group"] == group]
    matrix = np.vstack([curve["raw"] for curve in group_curves])
    mean = matrix.mean(axis=0)
    deviation = matrix.std(axis=0, ddof=1)
    axis.plot(grid, mean, color=colors[group], linewidth=2, label=f"{group} (n=2)")
    axis.fill_between(grid, mean - deviation, mean + deviation, color=colors[group], alpha=0.10, linewidth=0)
axis.axhline(0, color="black", linewidth=0.6)
axis.set_xlabel("Ewe / V vs SCE")
axis.set_ylabel("I / mA")
axis.set_title("2026-07-17 N719 A–K: mean LSV ± SD (6x6 excluded)")
axis.legend(ncol=4, fontsize=8)
fig.tight_layout()
fig.savefig(FIG_DIR / "20260717_a-k_lsv_mean_sd.png", dpi=220)
plt.close(fig)

fig, axes = plt.subplots(3, 2, figsize=(12, 13), sharex=True)
for axis, group in zip(axes.flat, REFERENCE_GROUPS):
    reference_matrix = np.vstack(
        [curve["raw"] for curve in reference_curves if curve["group"] == group]
    )
    current_matrix = np.vstack(
        [curve["raw"] for curve in current_curves if curve["group"] == group]
    )
    reference_mean = reference_matrix.mean(axis=0)
    reference_sd = reference_matrix.std(axis=0, ddof=1)
    current_mean = current_matrix.mean(axis=0)
    current_sd = current_matrix.std(axis=0, ddof=1)
    axis.plot(grid, reference_mean, color="#74645d", linewidth=2, label="2026-07-13")
    axis.fill_between(grid, reference_mean - reference_sd, reference_mean + reference_sd, color="#74645d", alpha=0.13)
    axis.plot(grid, current_mean, color="#d85f24", linewidth=2, label="2026-07-17")
    axis.fill_between(grid, current_mean - current_sd, current_mean + current_sd, color="#d85f24", alpha=0.13)
    decision = next(item for item in identification_json if item["group"] == group)
    axis.set_title(f"Board {group.upper()} — {decision['result'].replace('_', ' ')}")
    axis.axhline(0, color="black", linewidth=0.5)
    axis.set_ylabel("I / mA")
    axis.legend(fontsize=8)
axes.flat[-1].axis("off")
for axis in axes[-1, :]:
    axis.set_xlabel("Ewe / V vs SCE")
fig.suptitle("A–E cross-date LSV comparison", fontsize=15)
fig.tight_layout(rect=[0, 0, 1, 0.98])
fig.savefig(FIG_DIR / "20260717_a-e_crossdate_overlay.png", dpi=220)
plt.close(fig)

for kind in ["raw", "maxabs", "zshape"]:
    matrix = np.array(
        [
            [
                next(
                    row["rmse"]
                    for row in cross_distance_rows[kind]
                    if row["query_group"] == query and row["reference_group"] == reference
                )
                for reference in REFERENCE_GROUPS
            ]
            for query in REFERENCE_GROUPS
        ]
    )
    fig, axis = plt.subplots(figsize=(7.2, 6.4))
    image = axis.imshow(matrix, cmap="magma")
    axis.set_xticks(range(len(REFERENCE_GROUPS)), labels=[item.upper() for item in REFERENCE_GROUPS])
    axis.set_yticks(range(len(REFERENCE_GROUPS)), labels=[item.upper() for item in REFERENCE_GROUPS])
    axis.set_xlabel(f"{REFERENCE_DATE} reference")
    axis.set_ylabel(f"{CURRENT_DATE} query")
    axis.set_title(f"A–E cross-date {METRIC_LABELS[kind]} RMSE")
    threshold = (matrix.max() + matrix.min()) / 2
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            value = matrix[row_index, column_index]
            axis.text(
                column_index,
                row_index,
                f"{value:.3f}",
                ha="center",
                va="center",
                color="white" if value < threshold else "black",
                fontsize=9,
            )
        axis.add_patch(Rectangle((row_index - 0.5, row_index - 0.5), 1, 1, fill=False, edgecolor="#1f8f4a", linewidth=2))
    colorbar = fig.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    colorbar.set_label("RMSE")
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"20260717_a-e_crossdate_{kind}_rmse.png", dpi=220)
    plt.close(fig)

figure_map = {
    "20260717_a-k_lsv_mean_sd.png": "rmse-20260717-a-k-group-means.png",
    "20260717_a-e_crossdate_overlay.png": "rmse-20260717-a-e-crossdate-overlay.png",
    "20260717_a-e_crossdate_raw_rmse.png": "rmse-20260717-crossdate-raw.png",
    "20260717_a-e_crossdate_maxabs_rmse.png": "rmse-20260717-crossdate-maxabs.png",
    "20260717_a-e_crossdate_zshape_rmse.png": "rmse-20260717-crossdate-zshape.png",
}
for source_name, destination_name in figure_map.items():
    shutil.copy2(FIG_DIR / source_name, SITE_FIG_DIR / destination_name)

# Human-readable lab report.
report = [
    "# 2026-07-17 N719 LSV update",
    "",
    "This dataset records the 2026-07-17 EC-Lab LSV measurements for boards A–K.",
    "",
    "## Inclusion",
    "",
    "- Included: boards `A–K`, two scans per board.",
    "- Excluded: the separately labelled `6x6` board, by instruction.",
    "- Boards `A–E` are compared with their 2026-07-13 enrollment templates.",
    "- Boards `F–K` are first measurements and receive no cross-date identity verdict.",
    "",
    "## Cross-date decision rule",
    "",
    "For A–E, each 2026-07-17 mean curve and both repeat scans are compared with the 2026-07-13 A–E mean templates using raw-current, max-abs-normalized, and z-score-shape RMSE.",
    "",
    "A board is called **recognizable** only if both normalized views (max-abs and z-score) select its own 2026-07-13 template for the group mean and both new scans, and the same-label distance remains within the provisional 2026-07-13 leave-one-out enrollment band. Raw-current RMSE is supplemental because current magnitude is especially sensitive to aging and session conditions.",
    "",
    "## A–E result",
    "",
    "**No A–E board passes both normalized cross-date views in this exploratory two-repeat test.**",
    "",
    "| board | I@0 V: 7/13 → 7/17 (mA) | raw nearest | max-abs nearest | z-shape nearest | same-label / 7/13 band (raw / max / z) | conclusion |",
    "|---|---:|---:|---:|---:|---:|---|",
]
for item in identification_json:
    group = item["group"]
    report.append(
        f"| {group.upper()} | {item['referenceIAt0VmA']:.3f} → {item['queryIAt0VmA']:.3f} "
        f"({item['iAt0VChangePercent']:.1f}%) | "
        f"{item['metrics']['raw']['nearestReference'].upper()} | "
        f"{item['metrics']['maxabs']['nearestReference'].upper()} | "
        f"{item['metrics']['zshape']['nearestReference'].upper()} | "
        f"{item['metrics']['raw']['sameLabelOverReferenceBand']:.1f}× / "
        f"{item['metrics']['maxabs']['sameLabelOverReferenceBand']:.1f}× / "
        f"{item['metrics']['zshape']['sameLabelOverReferenceBand']:.1f}× | {item['status']} |"
    )
report += [
    "",
    "Single-view nearest-label signals are not successful re-identification: A points to itself only in z-score shape, B only in max-abs normalization, and D only in raw current; all three same-label distances remain outside their 2026-07-13 leave-one-out bands. C and E do not return their own prior label in any group-mean view.",
    "",
    "## F–K first-measurement baseline",
    "",
    "| board | n | I@0 V mean (mA) | I@0 V sd | zero-cross mean (V vs SCE) |",
    "|---|---:|---:|---:|---:|",
]
for row in group_rows:
    if row["group"] not in FIRST_MEASUREMENT_GROUPS:
        continue
    zero_text = (
        f"{row['zero_cross_E_V_vs_SCE_mean']:.4f}"
        if not math.isnan(row["zero_cross_E_V_vs_SCE_mean"])
        else "not observed in sweep"
    )
    report.append(
        f"| {row['group'].upper()} | {row['n_scans']} | {row['I_at_0V_mA_mean']:.4f} | "
        f"{row['I_at_0V_mA_sd']:.4f} | {zero_text} |"
    )
report += [
    "",
    "## Measurement metadata",
    "",
    "- Technique: Linear Sweep Voltammetry (LSV)",
    "- Instrument export: EC-Lab ASCII text",
    "- Reference electrode: SCE (Saturated Calomel Electrode)",
    "- Scan setting from headers: Ei = -0.800 V vs Ref, EL = 0.010 V vs Ref, scan rate = 10 mV/s",
    "- Electrolyte header: NaCl (0.2 M); comment: Fe(CN)6^3-/Fe(CN)6^4- 5×10^-3 M",
    "- Initial zero-current stabilization rows are removed before RMSE/shape analysis.",
    "",
    "## Reproduce",
    "",
    "```bash",
    "python3 -m pip install -r requirements-analysis.txt",
    "python3 scripts/analyze_20260717_n719.py",
    "```",
    "",
    "## Limits",
    "",
    "- This is an exploratory comparison with only two 2026-07-17 repeats per board.",
    "- Temperature, illumination, contact pressure, and electrolyte/aging state were not modeled as separate covariates.",
    "- The decision rule was applied retrospectively and must be validated prospectively on later sessions.",
    "- The acquisition headers match on instrument/channel, SCE, electrolyte, sweep range, and scan rate, but the loaded EC-Lab setting-file path differs between dates and should be checked at the next controlled session.",
    "- Voltage points are sorted for interpolation; raw files remain preserved because sorting can hide acquisition-order or hysteresis effects.",
    "- A failed cross-date nearest-template result does not prove two physical boards are identical; it means the present curve representation cannot reliably recover the enrolled label.",
    "- These results do not establish a production PUF, unclonability, or long-term identity.",
    "",
    "## Files",
    "",
    "- `raw/ec-lab-txt/`: 22 included A–K EC-Lab text exports",
    "- `raw/SHA256SUMS.txt`: raw-file checksums",
    "- `processed/scan_metrics.csv`: per-scan features",
    "- `processed/group_summary.csv`: 2026-07-17 group summaries",
    "- `processed/cross_date_identification.csv`: A–E decision table",
    "- `processed/reference_leave_one_out.csv`: provisional 7/13 enrollment-variation bands",
    "- `processed/cross_date_*_distance_matrix.csv`: full 7/17-to-7/13 RMSE matrices",
    "- `processed/iv_analysis_20260717.json`: site and machine-readable payload",
    "- `figures/`: A–K and cross-date visualizations",
]
(DATA_DIR / "README.md").write_text("\n".join(report) + "\n")

print(f"Analyzed {len(current_curves)} current scans across A–K; excluded 6x6")
print(f"Reference enrollment: {len(reference_curves)} scans across A–E")
print("Robust A–E matches:", [item["group"] for item in identification_json if item["result"] == "recognizable"])
print(DATA_DIR)
