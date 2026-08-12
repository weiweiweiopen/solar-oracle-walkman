# Solar Oracle Walkman Project Dashboard

Last updated: 2026-08-12

## Current project status

**Accurate description:** PUF-inspired weak-PUF / physical-fingerprint prototype.

Solar Oracle Walkman currently identifies an enrolled cell with a 16-point I-V curve, a Conv1D normalized-shape classifier, a 7D physical-fingerprint distance, and an open-set threshold. An accepted identity event can then generate an event SHA-256 and start the six-channel World Radio Mixtable.

The project has **not** established a fixed board identity key (K1), a stable fuzzy-extractor reconstruction pipeline, or a strong-PUF security result.

## Evidence dashboard

| Workstream | Status | Current evidence | Decision |
| --- | --- | --- | --- |
| N719-G / N719-B enrolled prototype | Limited pass | Paired-session validation reached 100% on the small two-cell enrolled dataset | Keep active as a prototype; do not generalize to PUF security |
| Silicon S1 / S2 candidate | Rejected | Conv1D 30.6%; 7D 31.1%; Voc + Isc 63.9%; combined 50.0% | Do not activate or weaken thresholds |
| Fixed K1 reconstruction | Not established | No accepted stable bit-selection, quantization, error-correction, or fuzzy-extractor result | Continue as a research target |
| Four-tester acquisition | Planned | Mac mini M4 and USB topology selected; concurrent software and inter-tester calibration are not implemented | One-tester SOP first, then expand |
| 100-cell campaign | Planned | Protocol and acceptance gates defined; large-volume measurements have not started | Target September 2026 after pilot gate |
| Three-month packaging evidence | Planned | Current evidence is approximately two weeks | Measure D0/1/3/7/14/30/60/90 |

## Identity and hash boundary

Current decision path:

`16-point I-V curve -> Conv1D normalized shape -> 7D distance -> open-set threshold -> identity decision -> event SHA-256 -> World Radio Mixtable`

- `oracle_hash`: SHA-256 of one identification JSON; it may change between measurements.
- `mix_sha256`: SHA-256 of one World Radio mapping.
- `model_sha256`: SHA-256 of the model file.
- Fixed board identity hash / K1: not established.

Recorded reference hashes:

- Latest N719-B event: `0x97025321b4b11f2bd00b9cabdf24a5221baaa17fe4416c78d405efb210c19360`
- Active N719 G/B model: `0x41f7d9ffbf0cd788f50ed7af2428b0f85a3c810b186ea6c7c0a8bb6f46e2564b`

## September 2026 campaign

Target population: up to 100 existing 3 x 3 cm DSSCs.

Minimum protocol:

- 5 independent sessions per cell
- 5 curves per session
- approximately 2,500 valid curves per condition
- D0, D1, D3, D7, D14, D30, D60, and D90
- independent reseating in every session
- interleaved cell, tester, and fixture-position order
- irradiance, spectrum, distance, angle, cell temperature, contact pressure, fixture position, tester ID, batch ID, packaging date, and reference-cell response recorded

Continuous scans without reseating are repeats, not independent sessions.

## PM timeline

### August: qualification exams first; SBIR in preparation mode

- 12-16 Aug: freeze protocol v0.1 and the acquisition schema; audit one tester's complete load paths.
- 17-20 Aug: protect qualification-exam study time; use one short block for fixture/BOM/reference-sensor inventory.
- 21-27 Aug: Post-Regeneration installation and preview blackout; no critical experiments.
- 28-30 Aug: close KPI C from supported evidence; do not manufacture a K1 claim.
- 31 Aug-2 Sep: reset the bench, label cells/testers, and prepare the pilot.

### September: gated ramp

- 3-4 Sep: one-tester dry run.
- 5-6 Sep: calibrate tester A and lock fixture geometry/reference baseline.
- 7-8 Sep: integrate additional testers only if A passes; separately prepare the 9 Sep e-embroidery gathering.
- 9 Sep: e-embroidery gathering; no SBIR critical-path work.
- 10-12 Sep: 10-cell interleaved pilot with independent reseating.
- 13-15 Sep: review tester/position effects and make the go/no-go decision.
- From 16 Sep: begin the 100-cell D0 campaign only after the start gate passes.

## Start gate for large-volume measurement

All must pass before the 100-cell campaign:

1. Unique cell, tester, fixture, and session IDs.
2. Documented reference-cell repeatability tolerance.
3. Complete load-path calibration for each active tester.
4. Repeatable fixture geometry and contact pressure.
5. Tested USB reconnect and per-device failure isolation.
6. Automatic metadata-completeness checks.
7. Pilot result without dominant tester or fixture-position label leakage.

If the four-tester system is late, run a controlled one-tester pilot instead of collecting a larger confounded dataset.

## K1 acceptance criteria

Do not claim stable K1 until at least:

- cross-session identity accuracy >= 95%
- same-device K1 reconstruction >= 99%
- inter-device Hamming distance near 50%
- balanced bit distribution
- no observed K1 collision
- FAR and FRR with confidence intervals
- helper data shown not to expose K1
- an old USB response cannot pass a fresh challenge
- reconstruction survives independent reseating and preferably calibrated tester changes

When controlled response distributions still overlap, report that the devices are electrically indistinguishable under this tester. Do not weaken the gate.

## Open PM dependencies

- Exact dates and submission deadlines for the three qualification-exam subjects.
- Named owners for fixture fabrication, tester replication, software, measurement operation, and daily QC.
- Numerical reference-cell tolerance for the D0 start gate.
- Confirm whether all 100 cells are already fabricated, labeled, and packaged.

## Evidence update rule

Preserve raw data and rejected results. When a new experiment conflicts with this dashboard, keep the original measurements and update the conclusion with the new protocol, date, evidence path, and deployment decision. Never rewrite a research hypothesis as a validated outcome.
