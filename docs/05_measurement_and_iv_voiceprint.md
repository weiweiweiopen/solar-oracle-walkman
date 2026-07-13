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
