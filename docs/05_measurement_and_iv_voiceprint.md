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
