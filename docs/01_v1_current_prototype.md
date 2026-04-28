# V1 Current Prototype

This repository already contains a V1 prototype built around the Solidity contract `SolarOracleWalkman`.

## What exists in V1

- Solidity contract: `SolarOracleWalkman`.
- IV voiceprint validation logic for 7-value input (`uint256[7]`).
- EIP-712 typed data signature verification for oracle-signed reports.
- Configurable oracle signer address.
- Timestamp freshness checks (`maxStaleness`).
- Duplicate IV hash prevention.
- On-chain storage of accepted IV records.
- Sepolia deployment details documented in `README.md`.
- Visual evidence in this repo:
  - DIY DSSC image (`pix/DIY_DSSC_with_cyanotype_pattern.jpg`)
  - I–V tester image (`pix/I-V_tester_made_by_Marc_Dusseiller.jpg`)

## Current limitations

- V1 does not yet prove a full PUF security model.
- V1 does not yet include a complete measurement hardware pipeline.
- V1 does not yet implement legal REC/T-REC functionality.
- V1 does not yet prove resistance against all replay, relay, or modeling attacks.
- V1 is a prototype for recording and validating IV voiceprint-like data, not a complete energy certification system.
