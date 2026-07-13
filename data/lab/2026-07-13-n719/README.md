# 2026-07-13 N719 LSV update

This dataset records the 2026-07-13 EC-Lab LSV measurements added to the Solar Oracle Walkman / DSSC-PUF working record.

## Inclusion note

- Included groups: `0, a, b, c, d, e`.
- Excluded groups: `1`, `2`.
- Reason: N719-1 and N719-2 from 2026-07-13 are excluded because sample labels may have been swapped.

## Measurement metadata

- Technique: Linear Sweep Voltammetry (LSV)
- Instrument export: EC-Lab ASCII text
- Reference electrode: SCE (Saturated Calomel Electrode)
- Scan setting from headers: Ei = -0.800 V vs Ref, EL = 0.010 V vs Ref, scan rate = 10 mV/s
- Electrolyte header: NaCl (0.2 M); comment: Fe(CN)6^3-/Fe(CN)6^4- 5×10^-3 M
- Initial zero-current stabilization rows were removed before RMSE/shape analysis.

## Group summary

| group | n | I@0 V mean (mA) | I@0 V sd | zero-cross mean (V vs SCE) |
|---|---:|---:|---:|---:|
| 0 | 5 | 4.5575 | 0.0861 | -0.6731 |
| a | 5 | 2.5249 | 0.0195 | -0.5769 |
| b | 5 | 3.1981 | 0.0218 | -0.6093 |
| c | 3 | 1.3068 | 0.0590 | -0.2606 |
| d | 5 | 2.1189 | 0.0311 | -0.4186 |
| e | 3 | 1.5063 | 0.0053 | -0.2324 |

## Included-groups RMSE summary

| kind | intra mean | intra max | inter mean | inter min | inter_min / intra_max |
|---|---:|---:|---:|---:|---:|
| raw | 0.0755 | 0.2903 | 1.7359 | 0.2547 | 0.88 |
| maxabs | 0.0183 | 0.0755 | 0.4287 | 0.0127 | 0.17 |
| zshape | 0.0086 | 0.0199 | 0.1242 | 0.0147 | 0.74 |

## Interpretation

The 2026-07-13 data should be used as additional evidence for short-term repeatability and device-to-device separability among the included groups. It should not be used as proof that every DSSC identity remains stable forever. N719-1 and N719-2 from this date remain excluded until label ambiguity is resolved by re-measurement.

## Files

- `raw/ec-lab-txt/`: included EC-Lab text exports
- `processed/scan_metrics.csv`: per-scan features
- `processed/group_summary.csv`: group-level mean and standard deviation
- `processed/rmse_summary.csv`: intra/inter RMSE summary
- `processed/*_rmse_pairwise.csv`: pairwise RMSE tables
- `figures/`: LSV overlay and RMSE heatmaps
