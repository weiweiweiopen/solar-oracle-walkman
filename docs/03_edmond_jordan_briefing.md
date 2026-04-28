# Edmond Jordan Technical Briefing

## Purpose
This page is a fast technical briefing for Edmond Jordan as advisor/reviewer.

## What exists now
- V1 IV voiceprint smart contract (`SolarOracleWalkman`).
- 7-value IV input validation.
- EIP-712 oracle signature verification.
- On-chain record storage and duplicate IV hash prevention.
- Sepolia deployment details in `README.md`.
- Visual context for DIY DSSC and I–V test setup in `pix/`.

## What needs technical validation
- Feature adequacy of the current 7-value vector.
- Measurement repeatability across time and environmental drift.
- Challenge-response design for material event evidence.
- Raw sweep data handling and reproducibility practices.
- Claims boundary between prototype evidence and stronger PUF/security claims.

## Questions for Edmond Jordan
1. Are the 7 IV-derived features meaningful enough for a first identity vector?
2. What measurement protocol is needed to test uniqueness and reliability?
3. What environmental variables must be controlled?
4. What is the minimum viable challenge-response space?
5. What should be done before making stronger PUF claims?
6. How should raw IV sweep data be stored?
7. How should the public registry separate example data from real measurement data?
