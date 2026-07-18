# Measurement and IV Voiceprint

## What is an I–V curve?
An I–V (current-voltage) curve describes how current changes as voltage changes for a solar cell under a given measurement condition.

## Why might a handmade/patterned DSSC show unique behavior?
A handmade or patterned DSSC can exhibit material and fabrication variability (surface patterning, interfaces, dye behavior, and assembly differences). Those differences may appear as distinct electrical response patterns in measured I–V behavior.

## What is a 7D IV voiceprint?
In this project, a 7D IV voiceprint is a compact seven-feature vector derived from I–V measurements, used as a candidate identity-like signal for validation and storage workflows.

Suggested feature vector:
- `FF`
- `Vmpp_over_Voc`
- `Impp_over_Isc`
- `Rs_star`
- `Rsh_star`
- `curvature_sum`
- `area_star`

These features are candidates for characterization, not yet final cryptographic proof.

## 2026-07-13 N719 LSV dataset update

A new EC-Lab LSV dataset was added at `data/lab/2026-07-13-n719/`.

Included in the repository update:

- N719 group `0`
- N719 groups `a`, `b`, `c`, `d`, `e`

Excluded from this update:

- N719 group `1` from 2026-07-13
- N719 group `2` from 2026-07-13

Reason: the 2026-07-13 lab labels for N719-1 and N719-2 may have been swapped, so they are not used as formal records until re-measurement resolves the ambiguity.

The included 2026-07-13 dataset is useful for short-term repeatability and device-to-device separability checks. It should not be treated as proof that every DSSC identity remains stable forever.

## 2026-07-17 A–K and cross-date update

The 2026-07-17 dataset is stored at `data/lab/2026-07-17-n719/`.

- Included: boards `A–K`, with two scans per board.
- Excluded: the separately labelled `6x6` board.
- Boards `A–E`: compared with their 2026-07-13 enrollment templates.
- Boards `F–K`: recorded as first-measurement baselines only.

The exploratory A–E check uses raw-current, max-abs-normalized, and z-score-shape RMSE on a shared voltage range. A board is accepted only when both normalized views return the expected prior label for the group mean and both repeat scans, while remaining within a provisional 2026-07-13 leave-one-out enrollment band.

No A–E board passed that cross-date rule. A returned its own label only in the z-score view, B only in the max-abs view, and D only in raw current; these same-label distances were still outside the enrollment bands. C and E did not return their prior labels in any group-mean view.

This means the current representation cannot reliably recover the 2026-07-13 A–E labels from the 2026-07-17 measurements. It does not prove permanent physical identity loss. Current magnitude fell strongly between sessions, and the experiment did not separately control aging, illumination, temperature, contact pressure, or electrolyte state.
