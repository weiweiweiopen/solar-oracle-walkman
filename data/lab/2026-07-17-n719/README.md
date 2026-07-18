# 2026-07-17 N719 LSV update

This dataset records the 2026-07-17 EC-Lab LSV measurements for boards A–K.

## Inclusion

- Included: boards `A–K`, two scans per board.
- Excluded: the separately labelled `6x6` board, by instruction.
- Boards `A–E` are compared with their 2026-07-13 enrollment templates.
- Boards `F–K` are first measurements and receive no cross-date identity verdict.

## A–E data-quality flag

**Status: `suspect_shared_hse_batch`.** The experimenter later reported that all A–E boards used the same HSE bottle after a pipette tip had fallen into it. The tip's prior contents, cleanliness, and residence time are unknown, so this is a suspected batch confound rather than proof that the HSE caused the low current.

The EC-Lab exports are structurally valid acquisitions, but this shared solution condition makes the A–E cross-date identity verdict **inconclusive pending controlled remeasurement**. It does not prove that the HSE caused the shift; A–E were also acquired as one later block (14:59–15:22), after F–K (13:55–14:56), so solution, time/order, contact, wetting, and electrode-condition effects are confounded.

## Cross-date decision rule

For A–E, each 2026-07-17 mean curve and both repeat scans are compared with the 2026-07-13 A–E mean templates using raw-current, max-abs-normalized, and z-score-shape RMSE.

A board is called **recognizable** only if both normalized views (max-abs and z-score) select its own 2026-07-13 template for the group mean and both new scans, and the same-label distance remains within the provisional 2026-07-13 leave-one-out enrollment band. Raw-current RMSE is supplemental because current magnitude is especially sensitive to aging and session conditions.

## A–E matcher result

**No A–E board passes both normalized cross-date views. Because of the shared suspected HSE-batch confound, the scientific identity verdict is inconclusive rather than permanent identity loss.**

| board | I@0 V: 7/13 → 7/17 (mA) | raw nearest | max-abs nearest | z-shape nearest | same-label / 7/13 band (raw / max / z) | conclusion |
|---|---:|---:|---:|---:|---:|---|
| A | 2.525 → 0.469 (-81.4%) | D | B | A | 15.0× / 14.8× / 7.2× | Inconclusive pending controlled remeasurement — A–E share a suspected HSE-batch confound. Matcher outcome: Not re-identified — only z-score shape chose the expected label, and the distance exceeded enrollment variation. |
| B | 3.198 → 1.027 (-67.9%) | A | B | A | 27.1× / 36.0× / 19.6× | Inconclusive pending controlled remeasurement — A–E share a suspected HSE-batch confound. Matcher outcome: Not re-identified — only max-abs normalized chose the expected label, and the distance exceeded enrollment variation. |
| C | 1.307 → 0.126 (-90.3%) | D | D | A | 14.0× / 15.0× / 15.2× | Inconclusive pending controlled remeasurement — A–E share a suspected HSE-batch confound. Matcher outcome: Not re-identified against the 2026-07-13 references. At least one matcher view assigns the two repeat scans differently. |
| D | 2.119 → 0.309 (-85.4%) | D | B | A | 7.5× / 10.6× / 10.5× | Inconclusive pending controlled remeasurement — A–E share a suspected HSE-batch confound. Matcher outcome: Not re-identified by normalized shape — raw current chose the expected label, but its distance exceeded enrollment variation. At least one matcher view assigns the two repeat scans differently. |
| E | 1.506 → 0.301 (-80.0%) | D | D | B | 7.8× / 16.5× / 30.5× | Inconclusive pending controlled remeasurement — A–E share a suspected HSE-batch confound. Matcher outcome: Not re-identified against the 2026-07-13 references. At least one matcher view assigns the two repeat scans differently. |

Single-view nearest-label signals are not successful re-identification: A points to itself only in z-score shape, B only in max-abs normalization, and D only in raw current; all three same-label distances remain outside their 2026-07-13 leave-one-out bands. C and E do not return their own prior label in any group-mean view.

These are matcher outputs, not a clean material-identity test, because every A–E query shares the newly reported HSE-bottle condition.

## A–E short-interval repeat check

| board | I@0 V scan 1 → scan 2 (mA) | repeat z-shape RMSE | assessment |
|---|---:|---:|---|
| A | 0.468430 → 0.468883 | 0.076 | good short-term repeat of a low-current state |
| B | 1.009932 → 1.043728 | 0.038 | good short-term repeat of a low-current state |
| C | 0.000327 → 0.251895 | 0.273 | poor; the two scans differ strongly |
| D | 0.306841 → 0.310700 | 0.073 | good short-term repeat of a low-current state |
| E | 0.289882 → 0.311991 | 0.048 | mixed; I@0 V is close, but the negative-potential branch changes |

A, B, and D show that the low-current state can repeat over a few minutes; that supports short-term precision but not accuracy. The same suspect solution, contact geometry, electrodes, and method can reproduce the same systematic bias twice. C is plainly unstable, and E retains a changing negative-potential branch.

## F–K first-measurement baseline

| board | n | I@0 V mean (mA) | I@0 V sd | zero-cross mean (V vs SCE) |
|---|---:|---:|---:|---:|
| F | 2 | 1.8099 | 0.0330 | not observed in sweep |
| G | 2 | 0.8899 | 0.0673 | -0.6732 |
| H | 2 | 0.6366 | 0.8972 | -0.2057 |
| I | 2 | 3.9823 | 0.4427 | -0.6222 |
| J | 2 | 3.8976 | 0.6655 | -0.6372 |
| K | 2 | 3.8681 | 0.2223 | -0.5761 |

F repeats well and K is reasonably shape-stable. G is moderate; H fails the repeat check (I@0 V 0.002 → 1.271 mA), while I and J show material magnitude shifts. F–K therefore remain provisional baselines rather than validated identities.

## Measurement metadata

- Technique: Linear Sweep Voltammetry (LSV)
- Instrument export: EC-Lab ASCII text
- Reference electrode: SCE (Saturated Calomel Electrode)
- Scan setting from headers: Ei = -0.800 V vs Ref, EL = 0.010 V vs Ref, scan rate = 10 mV/s
- Electrolyte header: NaCl (0.2 M); comment: Fe(CN)6^3-/Fe(CN)6^4- 5×10^-3 M
- Initial zero-current stabilization rows are removed before RMSE/shape analysis.

## Recommended controlled remeasurement

1. Quarantine and label the suspect HSE; do not return aliquots to fresh stock. Record HSE lot/preparation date, tip condition, temperature, illumination, equilibration time, electrode identity, and contact geometry.
2. If solution exchange is reversible without altering a board, use A and B as sentinels and test suspect HSE (`S`) versus independently fresh/verified HSE (`F`) with balanced order: A `S→F`, B `F→S`. Otherwise use matched sacrificial sentinels rather than re-filling A/B.
3. For each board × solution, acquire two scans without reseating and one after a force-defined reseat: 12 board LSVs total. Randomize board order and hold equilibration time constant.
4. Bracket the sequence with a stable electrochemical check cell in each solution at start/end and verify the SCE before/after.
5. Compare the archived 2026-07-13 and 2026-07-17 EC-Lab setting files directly; if they differ beyond displayed parameters, test the check cell under both programs.

This matrix separates a solution-wide shift from board contact/wetting, electrode/session drift, and persistent board aging more effectively than repeating the same unchanged setup twice.

## Reproduce

```bash
python3 -m pip install -r requirements-analysis.txt
python3 scripts/analyze_20260717_n719.py
```

## Limits

- This is an exploratory comparison with only two 2026-07-17 repeats per board.
- A–E carry the `suspect_shared_hse_batch` flag because they shared a potentially compromised HSE bottle; the exact contamination state is unknown.
- F–K were measured earlier and are different boards, so they are not a clean same-board or contemporaneous solution control for A–E.
- Temperature, illumination, contact pressure, wetting/bubbles, equilibration time, and electrolyte/aging state were not modeled as separate covariates.
- The decision rule was applied retrospectively and must be validated prospectively on later sessions.
- The acquisition headers match on instrument/channel, SCE, electrolyte, sweep range, and scan rate, but the loaded EC-Lab setting-file path differs between dates and should be checked at the next controlled session.
- Voltage points are sorted for interpolation; raw files remain preserved because sorting can hide acquisition-order or hysteresis effects.
- A failed cross-date nearest-template result does not prove two physical boards are identical; it means the present curve representation cannot reliably recover the enrolled label.
- These results do not establish a production PUF, unclonability, or long-term identity.

## Files

- `raw/ec-lab-txt/`: 22 included A–K EC-Lab text exports
- `raw/SHA256SUMS.txt`: raw-file checksums
- `processed/scan_metrics.csv`: per-scan features
- `processed/group_summary.csv`: 2026-07-17 group summaries
- `processed/cross_date_identification.csv`: A–E decision table
- `processed/reference_leave_one_out.csv`: provisional 7/13 enrollment-variation bands
- `processed/cross_date_*_distance_matrix.csv`: full 7/17-to-7/13 RMSE matrices
- `processed/iv_analysis_20260717.json`: site and machine-readable payload
- `figures/`: A–K and cross-date visualizations
