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

After the first analysis, the experimenter clarified that A–E were fabricated with HSE from an older bottle in which a pipette tip used only to aspirate that HSE had remained immersed for about 18 months. A–E were then sealed and were not refilled between 2026-07-13 and 2026-07-17. F–K used a separate, newer-year HSE bottle. Electrolyte age/batch, long tip exposure, and cell cohort are therefore inseparable; this does not prove which factor caused the low current.

A separate manufacturing confound affects dye loading. Boards 0, 1, and 2 used fourfold-concentration N719 freshly removed from refrigeration; subsequent boards, including A–K, used the same initially ~100 mL dye bath, which was reused without being returned to refrigeration. Repeated TiO2 uptake can lower dye concentration, while solvent evaporation can raise nominal concentration and alter solvent composition. Without UV–Vis, bath-volume, cumulative-area, light, temperature, and elapsed-time records, the direction and size of any concentration change are unknown.

Seal quality is an even more direct concern for the four-day decline. The boards used HI SUPER 30 two-part epoxy, and the experimenter reports that many seals had an incorrect A/B ratio, remained incompletely cured for a long time, and were stored together in one sealed bag. Off-ratio adhesive can leave unreacted resin or hardener and fail to form a durable barrier. Direct leaching at the fill seal, solvent loss, moisture/oxygen ingress, and bubble formation are plausible; shared-bag vapor transfer is secondary and unproven. The product date-code format and HSE compatibility have not been independently verified.

The EC-Lab files remain valid acquisitions, and the matcher still cannot recover the 2026-07-13 A–E labels from them. Because no new HSE or dye entered A–E between dates, the 2026-07-17 drop is a four-day change in the same sealed cells—not a new solution exposure on measurement day. A, B, and D repeat that low-current state over a few minutes, which supports short-term precision but not accuracy; C is unstable and E changes on its negative-potential branch. The identity verdict is **inconclusive pending correctly sealed matched manufacturing trajectories** that separate seal cure and compatibility, HSE age, tip immersion, dye-bath history, post-fabrication aging, illumination, temperature, contact pressure, wetting, acquisition order, and electrode state.
