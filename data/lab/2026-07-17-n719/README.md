# 2026-07-17 N719 LSV update

This dataset records the 2026-07-17 EC-Lab LSV measurements for boards A–K.

## Inclusion

- Included: boards `A–K`, two scans per board.
- Excluded: the separately labelled `6x6` board, by instruction.
- Boards `A–E` are compared with their 2026-07-13 enrollment templates.
- Boards `F–K` are first measurements and receive no cross-date identity verdict.

## A–E data-quality flag

**Status: `manufacturing_and_seal_confounded`.** A–E combine an aged-HSE cell cohort, a reused unrefrigerated N719 bath, and reportedly off-ratio, incompletely cured epoxy seals. These manufacturing conditions make the four-day identity comparison inconclusive; none is individually proven to have caused the current loss.

**HSE subflag: `aged_hse_sealed_cell_cohort`.** A–E were fabricated with HSE from an older bottle in which a pipette tip used only to aspirate that HSE had remained immersed for about 18 months. The cells were sealed after filling and were not refilled between 2026-07-13 and 2026-07-17. F–K used a separate, newer-year HSE bottle.

The EC-Lab exports are structurally valid acquisitions. Because A–E stayed sealed and received no new HSE between dates, the 2026-07-17 drop is a change in the same sealed cells over four days, not a fresh HSE exposure on measurement day. The newly reported off-ratio, incompletely cured epoxy makes seal-barrier failure, solvent loss, moisture/oxygen ingress, or direct leaching at the fill seal a leading explanation. HSE history, post-fabrication aging, contact, acquisition order, and electrode/session effects remain confounded.

A–E still produced 1.307–3.198 mA at 0 V on 2026-07-13 despite that fabrication history. The evidence therefore points to a rapid four-day trajectory change rather than cells that were inactive from the outset.

## Epoxy seal-quality flag

**Status: `off_ratio_incompletely_cured_epoxy_seals`.** The boards were sealed with HI SUPER 30 two-part epoxy. The experimenter reports that the A/B ratio was not correct on many boards, the adhesive remained incompletely cured for a long time, and the boards were stored together in one sealed bag. Direct leaching at the fill seal, barrier failure, solvent loss, and moisture/oxygen ingress are plausible; shared-bag vapor transfer is secondary and unproven.

Incorrect two-part stoichiometry can leave reactive resin or hardener and can prevent a durable barrier from forming even after long waiting. The shared sealed bag could permit some vapor transfer if seals were already imperfect, but each board's own under-cured fill seal is the more direct pathway. The photograph shows a HI SUPER 30 dual-cartridge product with lot code D2621 and use-by code 270420; the date-code format and HSE compatibility were not independently verified.

## N719 dye-bath quality flag

**Status: `reused_unrefrigerated_n719_bath`.** Boards 0, 1, and 2 used fourfold-concentration N719 freshly removed from refrigeration. Subsequent boards, including A–K, were stained from the same bath, initially about 100 mL, which was reused without being returned to refrigeration. Elapsed storage time, cumulative TiO2 area, final bath volume, light exposure, and temperature were not logged, so neither concentration loss nor chemical stability can be inferred from appearance alone.

Repeated TiO2 uptake can lower N719 concentration, but solvent evaporation can instead raise nominal concentration while changing solvent composition. Light, heat, moisture, and sample carry-over can also reduce effective staining quality. The current photographs and solution color cannot distinguish these mechanisms or quantify concentration. This dye-bath history can confound dye loading and board-to-board differences, but cannot by itself explain the four-day A–E decline because the cells were already sealed and functioning on 2026-07-13.

## Cross-date decision rule

For A–E, each 2026-07-17 mean curve and both repeat scans are compared with the 2026-07-13 A–E mean templates using raw-current, max-abs-normalized, and z-score-shape RMSE.

A board is called **recognizable** only if both normalized views (max-abs and z-score) select its own 2026-07-13 template for the group mean and both new scans, and the same-label distance remains within the provisional 2026-07-13 leave-one-out enrollment band. Raw-current RMSE is supplemental because current magnitude is especially sensitive to aging and session conditions.

## A–E matcher result

**No A–E board passes both normalized cross-date views. Because incompletely cured epoxy seals, aged-HSE history, and an unquantified reused N719 bath are uncontrolled manufacturing variables, the scientific identity verdict is inconclusive rather than permanent identity loss.**

| board | I@0 V: 7/13 → 7/17 (mA) | raw nearest | max-abs nearest | z-shape nearest | same-label / 7/13 band (raw / max / z) | conclusion |
|---|---:|---:|---:|---:|---:|---|
| A | 2.525 → 0.469 (-81.4%) | D | B | A | 15.0× / 14.8× / 7.2× | Inconclusive pending matched manufacturing controls — aged HSE, reused N719, and off-ratio incompletely cured epoxy seals are confounded. Matcher outcome: Not re-identified — only z-score shape chose the expected label, and the distance exceeded enrollment variation. |
| B | 3.198 → 1.027 (-67.9%) | A | B | A | 27.1× / 36.0× / 19.6× | Inconclusive pending matched manufacturing controls — aged HSE, reused N719, and off-ratio incompletely cured epoxy seals are confounded. Matcher outcome: Not re-identified — only max-abs normalized chose the expected label, and the distance exceeded enrollment variation. |
| C | 1.307 → 0.126 (-90.3%) | D | D | A | 14.0× / 15.0× / 15.2× | Inconclusive pending matched manufacturing controls — aged HSE, reused N719, and off-ratio incompletely cured epoxy seals are confounded. Matcher outcome: Not re-identified against the 2026-07-13 references. At least one matcher view assigns the two repeat scans differently. |
| D | 2.119 → 0.309 (-85.4%) | D | B | A | 7.5× / 10.6× / 10.5× | Inconclusive pending matched manufacturing controls — aged HSE, reused N719, and off-ratio incompletely cured epoxy seals are confounded. Matcher outcome: Not re-identified by normalized shape — raw current chose the expected label, but its distance exceeded enrollment variation. At least one matcher view assigns the two repeat scans differently. |
| E | 1.506 → 0.301 (-80.0%) | D | D | B | 7.8× / 16.5× / 30.5× | Inconclusive pending matched manufacturing controls — aged HSE, reused N719, and off-ratio incompletely cured epoxy seals are confounded. Matcher outcome: Not re-identified against the 2026-07-13 references. At least one matcher view assigns the two repeat scans differently. |

Single-view nearest-label signals are not successful re-identification: A points to itself only in z-score shape, B only in max-abs normalization, and D only in raw current; all three same-label distances remain outside their 2026-07-13 leave-one-out bands. C and E do not return their own prior label in any group-mean view.

These are matcher outputs, not a clean material-identity test, because the cohort combines reported seal-cure failures, aged-HSE history, and an unquantified reused N719 bath.

## A–E short-interval repeat check

| board | I@0 V scan 1 → scan 2 (mA) | repeat z-shape RMSE | assessment |
|---|---:|---:|---|
| A | 0.468430 → 0.468883 | 0.076 | good short-term repeat of a low-current state |
| B | 1.009932 → 1.043728 | 0.038 | good short-term repeat of a low-current state |
| C | 0.000327 → 0.251895 | 0.273 | poor; the two scans differ strongly |
| D | 0.306841 → 0.310700 | 0.073 | good short-term repeat of a low-current state |
| E | 0.289882 → 0.311991 | 0.048 | mixed; I@0 V is close, but the negative-potential branch changes |

A, B, and D show that the low-current state can repeat over a few minutes; that supports short-term precision but not accuracy. A degraded or leaking sealed-cell state, unchanged contact geometry, electrodes, and method can reproduce the same systematic bias twice. C is plainly unstable, and E retains a changing negative-potential branch.

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
- Cell fill reported by experimenter: HSE; A–E and F–K used different HSE bottles
- Seal reported by experimenter: HI SUPER 30 two-part epoxy; many boards had incorrect A/B ratio and remained incompletely cured
- EC-Lab header label: NaCl (0.2 M); comment: Fe(CN)6^3-/Fe(CN)6^4- 5×10^-3 M. This stored header does not verify the sealed-cell HSE batch.
- Initial zero-current stabilization rows are removed before RMSE/shape analysis.

## Recommended controlled remeasurement

1. Quarantine the poorly cured cell cohort, old HSE, and reused N719 bath. Keep A–E sealed; adding more epoxy or reopening them would create a new object, not restore the original identity trajectory.
2. Obtain the HI SUPER 30 technical data sheet and confirm the required A/B ratio, mixing method, full-cure schedule, date-code format, and chemical compatibility. Use the intended dual-cartridge plunger/static mixer or weigh components to the specified ratio; do not judge cure by elapsed time alone.
3. Before making identity cells, compare HSE alone, HSE with a fully cured correctly mixed epoxy coupon, and HSE with a retained suspect-seal coupon in separate sealed compatibility vials. Monitor appearance and, where available, UV–Vis/electrochemistry; avoid intentionally placing off-ratio adhesive into new cells.
4. With one verified seal process, fabricate a same-day 2×2 matched dummy-cell experiment: old versus fresh HSE crossed with reused versus fresh N719, at least three cells per condition (12 total). Compare reused and fresh N719 by identically diluted UV–Vis and log bath volume, TiO2 area, time, light, and temperature.
5. Measure fixed-condition trajectories after initial equilibration, 24 hours, 4 days, and 7 days. Photograph seals/bubbles, track cell mass if possible, store cells separately until full cure, and bracket sessions with a stable check cell and SCE verification.

This sequence first removes seal failure, then separates HSE history, dye-bath history, their interaction, ordinary aging, contact/wetting, and session drift without reopening A–E.

## PUF claim boundary: unsealed versus sealed

- **Track U — intrinsic electrode identity:** use an unsealed but fixture-defined gasket/spacer, active area, alignment, contact force, fresh-electrolyte volume, and equilibration time. Independently disassemble and reconstitute the same electrode across at least three sessions. One droplet followed by two scans proves only short-interval precision.
- **Track S — persistent device identity:** use the new verified seal process and monitor the same unopened DSSC at Day 0, 1, 4, 7, 14, and 30.
- Track U can establish re-readable solid-electrode identity without package failure; Track S is required for a self-contained long-lived device claim. Neither track alone establishes unclonability without a separate replication/attack experiment.

## Reproduce

```bash
python3 -m pip install -r requirements-analysis.txt
python3 scripts/analyze_20260717_n719.py
```

## Limits

- This is an exploratory comparison with only two 2026-07-17 repeats per board.
- A–E carry the overall `manufacturing_and_seal_confounded` flag because multiple manufacturing and sealing variables were uncontrolled.
- A–E carry the `aged_hse_sealed_cell_cohort` subflag: they were sealed with an older HSE batch that had contained a submerged pipette tip for about 18 months; no refilling occurred between dates.
- A–K carry the `reused_unrefrigerated_n719_bath` subflag because they used a reused N719 bath that was not returned to refrigeration; actual concentration and chemical stability were not measured.
- The cohort carries the `off_ratio_incompletely_cured_epoxy_seals` subflag because the reported epoxy A/B ratio was wrong on many boards and cure remained incomplete.
- F–K used a separate, newer-year HSE bottle and are different boards with no earlier baseline, so they are not a clean control for A–E.
- The present data cannot separate off-ratio adhesive/leaching, barrier failure, HSE age, long tip immersion, dye-bath depletion/composition, or ordinary post-fabrication aging as causes of the observed differences.
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
