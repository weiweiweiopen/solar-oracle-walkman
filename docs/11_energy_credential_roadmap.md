# Energy Credential Roadmap

Last updated: 2026-08-12

## Core rule

**Blockchain is not a green certificate.**

The intended evidence chain is:

`DSSC-PUF device authentication -> precision DC metering -> authenticated micro-energy events -> lossless aggregation -> private Green Proof lifecycle -> prospective DER verification methodology -> Issuer-reviewed I-REC(E)`

This is a roadmap. Solar Oracle does not currently issue Energy Web Green Proofs, hold an I-TRACK Verification Label, or issue I-REC(E).

## What each layer proves

### 1. DSSC-PUF

Target claim: which enrolled physical solar object submitted the event.

It does not prove energy volume. The current identity system remains a PUF-inspired weak-PUF / physical-fingerprint prototype, and stable K1 has not been established.

### 2. Precision DC metering

Target claim: how much energy was generated.

Power must be integrated over time. Each record must retain timestamps, meter identity, calibration, uncertainty, and raw evidence. An instantaneous `0.3 mW` reading is not `0.0003 Wh`.

### 3. Authenticated micro-energy events

A value such as `0.0003 Wh` can be an internal minimum event. It is not automatically an external EAC.

Planned event fields:

```text
event_id
device_id
PUF_verification_result
challenge_id_or_nonce
start_time
end_time
energy_Wh
meter_id
calibration_id
measurement_uncertainty
generation_type = solar_DSSC
previous_event_hash
event_hash
raw_evidence_uri
aggregation_status
retirement_or_redemption_status
```

### 4. Aggregation

Micro-events must remain traceable:

`0.0003 Wh + 0.0004 Wh + 0.0002 Wh + ... -> Wh -> kWh -> Issuer-acceptable volume evidence`

Every aggregate must resolve to its original events, physical devices, meter records, and audit state.

### 5. Energy Web Green Proofs

Phase 1 target: a private auditable registry proof of concept.

Energy Web documents configurable Green Proof registries and issue, transfer, and retirement operations. Green Proofs access requires a customized subscription or offer from Energy Web. This layer manages the private proof lifecycle; it does not perform DSSC identity recognition and is not I-REC(E).

Target private lifecycle:

`ISSUE -> TRANSFER -> BUYER -> RETIRE`

The pilot policy requires retirement to prevent reuse of the same environmental attribute.

### 6. I-TRACK Verification Label route

Phase 2 target: propose DSSC-PUF plus calibrated metering as part of a credible verification methodology for small distributed renewable facilities.

I-TRACK describes Verification Labels as supplementary or separate third-party verification methodologies that can support issuance where DER lacks conventional settlement-meter evidence. REDEX's approved Verification Label provides a precedent focused on devices below 250 kW.

Solar Oracle is not an approved Verification Label. The near-term objective is to test feasibility with I-TRACK, the Taiwan Issuer, and accredited partners—not to present Solar Oracle as another I-REC system.

### 7. I-REC(E)

I-REC(E) is the external EAC layer. Its primary unit is MWh, with optional resolution below MWh to Wh under the Product Code. A Registrant must register the production facility and request issuance through the authorized Issuer. An application cannot mint I-REC(E) by calling its own API.

I-TRACK expanded Taiwan eligibility from 1 January 2026 to include solar and wind facilities not receiving a Feed-in Tariff. The Green Certificate Company is the listed Issuer for Taiwan and checks requests against FiT registration and the T-REC Registry. This eligibility change does not automatically qualify handmade DSSCs.

## Planned API

- `POST /devices/enroll`
- `POST /devices/verify`
- `POST /energy-events`
- `POST /aggregate`
- `POST /proofs/issue`
- `POST /proofs/transfer`
- `POST /proofs/retire`
- `GET /audit`

These endpoints are a design target, not current verified implementation.

## Work packages

### Private Green Proof pilot

1. Complete Launchpad account readiness and request a Green Proofs demo/custom offer.
2. Define registry actors, units, evidence rules, approval authority, transfer rules, and retirement policy.
3. Integrate only after the internal event and aggregation model passes.
4. Recruit one EV/CPO or other counterparty willing to receive and retire an auditable batch.
5. Preserve the acceptance terms as evidence of whether the private institutional experiment worked.

### Device and meter evidence

1. Establish independent-session repeatability, inter-device uniqueness, FAR/FRR with confidence intervals, aging drift, anti-replay, and calibrated cross-tester behavior.
2. Add stable bit selection, quantization, error correction, and fuzzy extraction only after repeatable features exist.
3. Use calibrated DC energy metering with a documented uncertainty budget.
4. Bind each energy record to device verification without implying that the PUF measured Wh.
5. Preserve reversible aggregation and double-count prevention.

### I-TRACK feasibility

1. Prepare the technical evidence dossier.
2. Contact I-TRACK, GCC/Evident, REDEX, or another accredited partner.
3. Determine whether Solar Oracle can operate under an existing Verification Label or requires a new Labelling Authority proposal.
4. Pursue facility registration and issuance only after an Issuer accepts the method and facility eligibility.

## Stop conditions

- Unstable identity: do not bind environmental attributes to the device.
- Uncalibrated metering: do not issue even a private proof as measured generation.
- Non-auditable aggregation: stop registry integration.
- No counterparty acceptance and retirement: report the private-market experiment as unproven.
- Issuer rejection: preserve the research registry, but do not claim an achieved I-REC(E) pathway.
- A hash, token, or blockchain record alone is never evidence that renewable electricity was generated.

## Official references

- [Energy Web Green Proofs Quickstart](https://docs.energyweb.org/launchpad/generic-and-energy-services/green-proofs-as-a-service/green-proofs-as-a-service-quickstart-guide)
- [Energy Web Green Proof operations](https://docs.energyweb.org/energy-solutions/green-proofs-by-energy-web/use-cases-and-reference-implementations/green-proofs-as-a-service-gpsaas)
- [I-TRACK Labelling Authority and Verification Labels](https://www.trackingstandard.org/labelling-authority/)
- [First approved REDEX Verification Label](https://www.trackingstandard.org/i-track-foundations-first-approved-verification-label/)
- [Updated Taiwan issuance criteria](https://www.trackingstandard.org/updated-issuance-criteria-in-taiwan/)
- [I-TRACK Issuers](https://www.trackingstandard.org/issuers/)
- [I-REC(E) Product Code](https://www.trackingstandard.org/product-code/electricity/)
