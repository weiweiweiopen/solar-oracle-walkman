#!/usr/bin/env python3
"""Analyze 2026-07-13 N719 LSV records for Solar Oracle Walkman docs.

Important: this dataset intentionally excludes N719_0713-1-* and N719_0713-2-*
because the lab labels were uncertain in the 2026-07-13 measurement session.
"""
from __future__ import annotations

import csv
import json
import math
import re
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/lab/2026-07-13-n719"
RAW_DIR = DATA_DIR / "raw/ec-lab-txt"
PROCESSED_DIR = DATA_DIR / "processed"
FIG_DIR = DATA_DIR / "figures"
SITE_DATA_DIR = ROOT / "site/data"
INCLUDED_GROUPS = ["0", "a", "b", "c", "d", "e"]
EXCLUDED_NOTE = "N719-1 and N719-2 from 2026-07-13 are excluded because sample labels may have been swapped."

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)
SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)


def group_sample(path: Path) -> tuple[str, str]:
    m = re.search(r"N719_0713-([0abcde])-([0-9]+)_C06\.txt$", path.name)
    if not m:
        raise ValueError(f"Unexpected filename for included 2026-07-13 dataset: {path.name}")
    return m.group(1), f"{m.group(1)}-{m.group(2)}"


def read_ec_lab_txt(path: Path) -> tuple[np.ndarray, np.ndarray]:
    lines = path.read_text(errors="ignore").splitlines()
    n_header = 0
    for line in lines[:100]:
        m = re.search(r"Nb header lines\s*:\s*(\d+)", line)
        if m:
            n_header = int(m.group(1))
            break
    if not n_header:
        raise ValueError(f"Cannot find EC-Lab header length in {path}")
    header = lines[n_header - 1].split("\t")
    low = [h.lower() for h in header]
    e_idx = next((i for i, h in enumerate(low) if "ewe" in h and "/v" in h), None)
    if e_idx is None:
        e_idx = next(i for i, h in enumerate(low) if "ewe" in h)
    i_idx = next((i for i, h in enumerate(low) if "<i>" in h or "i/" in h), None)
    if i_idx is None:
        raise ValueError(f"Cannot find current column in {path}")

    E: list[float] = []
    I: list[float] = []
    for line in lines[n_header:]:
        parts = line.split("\t")
        if len(parts) <= max(e_idx, i_idx):
            continue
        try:
            e = float(parts[e_idx].replace(",", "."))
            i = float(parts[i_idx].replace(",", "."))
        except ValueError:
            continue
        # EC-Lab files include an initial zero-current stabilization/pre-hold segment.
        # Remove it from curve shape and RMSE calculations.
        if abs(i) > 1e-12:
            E.append(e)
            I.append(i)
    pairs = sorted(zip(E, I))
    return np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])


def interp_at(E: np.ndarray, I: np.ndarray, x: float) -> float:
    if x < E.min() or x > E.max():
        return math.nan
    return float(np.interp(x, E, I))


def zero_cross(E: np.ndarray, I: np.ndarray) -> float:
    for e0, i0, e1, i1 in zip(E[:-1], I[:-1], E[1:], I[1:]):
        if i0 == 0:
            return float(e0)
        if i0 * i1 < 0:
            return float(e0 - i0 * (e1 - e0) / (i1 - i0))
    return math.nan


def rmse(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(np.mean((a - b) ** 2)))


def norm_maxabs(y: np.ndarray) -> np.ndarray:
    m = np.max(np.abs(y))
    return y / m if m else y * 0


def norm_zscore(y: np.ndarray) -> np.ndarray:
    s = np.std(y)
    return (y - np.mean(y)) / s if s else y * 0


curves = []
for path in sorted(RAW_DIR.glob("*.txt")):
    group, sample = group_sample(path)
    E, I = read_ec_lab_txt(path)
    curves.append({"group": group, "sample": sample, "file": path.name, "E": E, "I": I})

if not curves:
    raise SystemExit("No included 2026-07-13 EC-Lab text files found.")

lo = max(float(c["E"].min()) for c in curves)
hi = min(float(c["E"].max()) for c in curves)
grid = np.linspace(lo, hi, 600)

for c in curves:
    raw = np.interp(grid, c["E"], c["I"])
    c["raw"] = raw
    c["maxabs"] = norm_maxabs(raw)
    c["zshape"] = norm_zscore(raw)

# Per-scan metrics.
scan_rows = []
for c in curves:
    E = c["E"]
    I = c["I"]
    scan_rows.append(
        {
            "date": "2026-07-13",
            "group": c["group"],
            "sample": c["sample"],
            "file": c["file"],
            "points_active": len(E),
            "E_min_V_vs_SCE": float(E.min()),
            "E_max_V_vs_SCE": float(E.max()),
            "I_min_mA": float(I.min()),
            "I_max_mA": float(I.max()),
            "I_at_-0.6V_mA": interp_at(E, I, -0.6),
            "I_at_-0.4V_mA": interp_at(E, I, -0.4),
            "I_at_-0.2V_mA": interp_at(E, I, -0.2),
            "I_at_0V_mA": interp_at(E, I, 0.0),
            "zero_cross_E_V_vs_SCE": zero_cross(E, I),
        }
    )

with (PROCESSED_DIR / "scan_metrics.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(scan_rows[0].keys()))
    writer.writeheader()
    writer.writerows(scan_rows)

# Group summary.
group_rows = []
for group in INCLUDED_GROUPS:
    rows = [r for r in scan_rows if r["group"] == group]
    if not rows:
        continue
    out = {"date": "2026-07-13", "group": group, "n_scans": len(rows)}
    for field in [
        "I_min_mA",
        "I_max_mA",
        "I_at_-0.6V_mA",
        "I_at_-0.4V_mA",
        "I_at_-0.2V_mA",
        "I_at_0V_mA",
        "zero_cross_E_V_vs_SCE",
    ]:
        vals = [r[field] for r in rows if not math.isnan(r[field])]
        out[field + "_mean"] = statistics.mean(vals) if vals else math.nan
        out[field + "_sd"] = statistics.stdev(vals) if len(vals) > 1 else 0.0
    group_rows.append(out)

with (PROCESSED_DIR / "group_summary.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(group_rows[0].keys()))
    writer.writeheader()
    writer.writerows(group_rows)

# RMSE analysis among included groups only.
pairs_by_kind = {}
summary_rows = []
for kind in ["raw", "maxabs", "zshape"]:
    pairs = []
    for i, a in enumerate(curves):
        for b in curves[i + 1 :]:
            value = rmse(a[kind], b[kind])
            pairs.append(
                {
                    "kind": kind,
                    "same_group": a["group"] == b["group"],
                    "group_pair": f"{a['group']}-{b['group']}",
                    "file_a": a["file"],
                    "file_b": b["file"],
                    "rmse": value,
                }
            )
    pairs_by_kind[kind] = pairs
    intra = [p["rmse"] for p in pairs if p["same_group"]]
    inter = [p["rmse"] for p in pairs if not p["same_group"]]
    summary_rows.append(
        {
            "kind": kind,
            "intra_mean": statistics.mean(intra),
            "intra_max": max(intra),
            "inter_mean": statistics.mean(inter),
            "inter_min": min(inter),
            "inter_min_over_intra_max": min(inter) / max(intra),
        }
    )
    with (PROCESSED_DIR / f"{kind}_rmse_pairwise.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(pairs[0].keys()))
        writer.writeheader()
        writer.writerows(pairs)

with (PROCESSED_DIR / "rmse_summary.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
    writer.writeheader()
    writer.writerows(summary_rows)

# Group mean RMSE matrix.
mean_rows = []
means: dict[tuple[str, str], np.ndarray] = {}
for kind in ["raw", "maxabs", "zshape"]:
    for group in INCLUDED_GROUPS:
        arr = [c[kind] for c in curves if c["group"] == group]
        if arr:
            means[(kind, group)] = np.mean(arr, axis=0)
    for idx, ga in enumerate(INCLUDED_GROUPS):
        for gb in INCLUDED_GROUPS[idx + 1 :]:
            if (kind, ga) in means and (kind, gb) in means:
                mean_rows.append({"kind": kind, "group_pair": f"{ga}-{gb}", "rmse": rmse(means[(kind, ga)], means[(kind, gb)])})

with (PROCESSED_DIR / "group_mean_rmse.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(mean_rows[0].keys()))
    writer.writeheader()
    writer.writerows(mean_rows)

# Site-oriented compact JSON with downsampled group means and metrics.
site_groups = []
for group in INCLUDED_GROUPS:
    arr = [c for c in curves if c["group"] == group]
    if not arr:
        continue
    raw_mean = np.mean([c["raw"] for c in arr], axis=0)
    raw_sd = np.std([c["raw"] for c in arr], axis=0, ddof=1) if len(arr) > 1 else np.zeros_like(raw_mean)
    # Downsample for browser display.
    idxs = np.linspace(0, len(grid) - 1, 160).astype(int)
    gsum = next(r for r in group_rows if r["group"] == group)
    site_groups.append(
        {
            "id": group,
            "title": f"N719 2026-07-13 Group {group}",
            "date": "2026-07-13",
            "replicates": len(arr),
            "included": True,
            "points": [[round(float(grid[i]), 6), round(float(raw_mean[i]), 6)] for i in idxs],
            "sdPoints": [[round(float(grid[i]), 6), round(float(raw_sd[i]), 6)] for i in idxs],
            "metrics": {k: v for k, v in gsum.items() if k not in {"date", "group"}},
        }
    )

site_payload = {
    "dataset": "N719_20260713_included_groups",
    "date": "2026-07-13",
    "xLabel": "Ewe (V vs SCE)",
    "yLabel": "Current <I> (mA)",
    "commonGrid_V_vs_SCE": [round(lo, 6), round(hi, 6)],
    "includedGroups": INCLUDED_GROUPS,
    "excludedGroups": ["1", "2"],
    "exclusionNote": EXCLUDED_NOTE,
    "groups": site_groups,
    "rmseSummary": summary_rows,
}

for path in [PROCESSED_DIR / "iv_analysis_20260713_included.json", SITE_DATA_DIR / "iv-analysis-20260713-included.json"]:
    path.write_text(json.dumps(site_payload, indent=2, ensure_ascii=False))

# Figures.
plt.style.use("seaborn-v0_8-whitegrid")
colors = {
    "0": "#4c78a8",
    "a": "#f58518",
    "b": "#54a24b",
    "c": "#e45756",
    "d": "#72b7b2",
    "e": "#b279a2",
}

fig, ax = plt.subplots(figsize=(10, 6))
for group in INCLUDED_GROUPS:
    arr = [c for c in curves if c["group"] == group]
    if not arr:
        continue
    mat = np.vstack([c["raw"] for c in arr])
    mean = mat.mean(axis=0)
    sd = mat.std(axis=0, ddof=1) if len(arr) > 1 else np.zeros_like(mean)
    ax.plot(grid, mean, color=colors[group], lw=2, label=f"group {group} (n={len(arr)})")
    ax.fill_between(grid, mean - sd, mean + sd, color=colors[group], alpha=0.13, linewidth=0)
ax.axhline(0, color="black", lw=0.6)
ax.set_xlabel("Ewe / V vs SCE")
ax.set_ylabel("I / mA")
ax.set_title("2026-07-13 N719 included groups: mean LSV ± SD")
ax.legend(ncol=2, fontsize=8)
fig.tight_layout()
fig.savefig(FIG_DIR / "20260713_included_groups_lsv_mean_sd.png", dpi=220)
plt.close(fig)

for kind, label in [("raw", "RMSE (mA)"), ("maxabs", "RMSE"), ("zshape", "RMSE")]:
    ordered = sorted(curves, key=lambda c: (INCLUDED_GROUPS.index(c["group"]), c["sample"]))
    matrix = np.zeros((len(ordered), len(ordered)))
    for i, a in enumerate(ordered):
        for j, b in enumerate(ordered):
            matrix[i, j] = rmse(a[kind], b[kind])
    fig, ax = plt.subplots(figsize=(9.5, 8))
    im = ax.imshow(matrix, cmap="viridis")
    ax.set_xticks(range(len(ordered)))
    ax.set_xticklabels([c["sample"] for c in ordered], rotation=90, fontsize=6)
    ax.set_yticks(range(len(ordered)))
    ax.set_yticklabels([c["sample"] for c in ordered], fontsize=6)
    ax.set_title(f"2026-07-13 included groups pairwise {kind} RMSE")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(label)
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"20260713_included_groups_{kind}_rmse_heatmap.png", dpi=220)
    plt.close(fig)

# Markdown report.
report = [
    "# 2026-07-13 N719 LSV update",
    "",
    "This dataset records the 2026-07-13 EC-Lab LSV measurements added to the Solar Oracle Walkman / DSSC-PUF working record.",
    "",
    "## Inclusion note",
    "",
    f"- Included groups: `{', '.join(INCLUDED_GROUPS)}`.",
    "- Excluded groups: `1`, `2`.",
    f"- Reason: {EXCLUDED_NOTE}",
    "",
    "## Measurement metadata",
    "",
    "- Technique: Linear Sweep Voltammetry (LSV)",
    "- Instrument export: EC-Lab ASCII text",
    "- Reference electrode: SCE (Saturated Calomel Electrode)",
    "- Scan setting from headers: Ei = -0.800 V vs Ref, EL = 0.010 V vs Ref, scan rate = 10 mV/s",
    "- Electrolyte header: NaCl (0.2 M); comment: Fe(CN)6^3-/Fe(CN)6^4- 5×10^-3 M",
    "- Initial zero-current stabilization rows were removed before RMSE/shape analysis.",
    "",
    "## Group summary",
    "",
    "| group | n | I@0 V mean (mA) | I@0 V sd | zero-cross mean (V vs SCE) |",
    "|---|---:|---:|---:|---:|",
]
for r in group_rows:
    report.append(
        f"| {r['group']} | {r['n_scans']} | {r['I_at_0V_mA_mean']:.4f} | {r['I_at_0V_mA_sd']:.4f} | {r['zero_cross_E_V_vs_SCE_mean']:.4f} |"
    )
report += [
    "",
    "## Included-groups RMSE summary",
    "",
    "| kind | intra mean | intra max | inter mean | inter min | inter_min / intra_max |",
    "|---|---:|---:|---:|---:|---:|",
]
for r in summary_rows:
    report.append(
        f"| {r['kind']} | {r['intra_mean']:.4f} | {r['intra_max']:.4f} | {r['inter_mean']:.4f} | {r['inter_min']:.4f} | {r['inter_min_over_intra_max']:.2f} |"
    )
report += [
    "",
    "## Interpretation",
    "",
    "The 2026-07-13 data should be used as additional evidence for short-term repeatability and device-to-device separability among the included groups. It should not be used as proof that every DSSC identity remains stable forever. N719-1 and N719-2 from this date remain excluded until label ambiguity is resolved by re-measurement.",
    "",
    "## Files",
    "",
    "- `raw/ec-lab-txt/`: included EC-Lab text exports",
    "- `processed/scan_metrics.csv`: per-scan features",
    "- `processed/group_summary.csv`: group-level mean and standard deviation",
    "- `processed/rmse_summary.csv`: intra/inter RMSE summary",
    "- `processed/*_rmse_pairwise.csv`: pairwise RMSE tables",
    "- `figures/`: LSV overlay and RMSE heatmaps",
]
(DATA_DIR / "README.md").write_text("\n".join(report) + "\n")

print(f"Analyzed {len(curves)} included scans across groups {', '.join(INCLUDED_GROUPS)}")
print(f"Common grid: {lo:.4f} to {hi:.4f} V vs SCE")
print(DATA_DIR)
