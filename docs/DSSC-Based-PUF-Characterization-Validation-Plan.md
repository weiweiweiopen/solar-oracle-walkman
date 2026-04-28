# DSSC-Based Physical Unclonable Function

**Characterization & Validation Plan**

**Version:** 1  
**Status:** Draft  
**Source:** PDF converted to Markdown for LLM-readable use  
**Confidentiality:** Confidential | Draft

---

## 1. Project Overview

This document defines the complete characterization and validation plan for a Dye-Sensitized Solar Cell (DSSC) based Physical Unclonable Function (PUF). The core concept exploits the inherent, uncontrollable manufacturing variability in DSSC fabrication to generate unique, device-specific cryptographic fingerprints without any secret key storage.

> **Core Concept:** Each DSSC, even when fabricated under identical nominal conditions, exhibits microscopically unique properties, including TiO2 morphology, dye loading density, electrolyte distribution, and grain boundaries. These differences produce measurably distinct electrical responses to the same optical/electrical stimulus, which forms the basis of PUF behavior.

### 1.1 Measurement Pipeline

All measurements follow a fixed pipeline from device stimulus through to computed PUF metrics.

**Figure 1: DSSC PUF Measurement Pipeline**

Controlled stimulus to PUF quality metrics:

1. DSSC device stimulus
2. Controlled stimulus, such as light, load, and temperature
3. Analog measurement, such as Isc, Voc, and I-V curve
4. Digitization and bit extraction, including thresholding into bits
5. Post-processing, including ECC and normalization
6. PUF metrics, including HD, BER, and entropy

### 1.2 PUF Quality Requirements

| Metric | Definition | Target |
|---|---|---|
| Uniqueness | Device-to-device variation in response bits | Inter-device Hamming distance approximately 50% |
| Reliability | Same device gives same response repeatedly | BER < 5% pre-ECC |
| Randomness | Response bits are statistically unpredictable | Pass NIST SP 800-22 tests |
| Stability | Robust to environmental changes | Stable across 20 deg C to 40 deg C |

### 1.3 Operating Constraints

- Operating temperature range: 20 deg C to 40 deg C
- All PUF metrics must be validated within this thermal window
- Temperature coefficients for Voc and Isc must be characterized and compensated if needed
- Long-term stability aging is a secondary goal; initial focus is functional PUF demonstration

---

## 2. DSSC Parameters for PUF Fingerprinting

The following parameters encode the unique physical identity of each DSSC and form the raw data from which PUF response bits are extracted.

### 2.1 Primary Electrical Parameters: High Priority

| Parameter | Symbol | Why It Is Unique | Measurement |
|---|---|---|---|
| Short-circuit current | Isc | Driven by dye loading density and TiO2 surface area | SMU at V=0 or transimpedance amp |
| Open-circuit voltage | Voc | Determined by quasi-Fermi level; sensitive to TiO2 morphology | High-impedance voltmeter or SMU |
| Fill Factor | FF | Encodes series resistance, including grain boundaries and contacts | Derived from I-V curve |
| Max power point | Pmax | Composite fingerprint: Voc x Isc x FF | Derived from I-V curve |
| Series resistance | Rs | Reflects grain structure and contact variation | I-V slope analysis |
| Shunt resistance | Rsh | Reflects unique leakage paths per device | I-V slope at Isc |

### 2.2 Dynamic / Transient Parameters

| Parameter | Why It Is Unique | Measurement Method |
|---|---|---|
| Rise time, light on | Electron injection rate depends on TiO2 particle connectivity | Oscilloscope or fast ADC >1 kHz |
| Decay time, light off | Recombination lifetime varies with dye coverage and electrolyte depth | Oscilloscope or fast ADC |
| Transient peak shape | Encodes multi-exponential processes driven by microscopic heterogeneity | Curve fitting on time-series |

### 2.3 Challenge-Response Parameter Space

| Challenge Axis | Variable | Example Values | CRP Contribution |
|---|---|---|---|
| Optical intensity | Irradiance [%] | 10%, 25%, 50%, 75%, 100% | 5 levels x N devices |
| Optical wavelength | LED color | Red (630 nm), Green (530 nm), Blue (470 nm), White | 4 wavelengths x N |
| Load condition | Resistance [Ohm] | 10, 100, 1k, 10k, open | 5 load points per sweep |
| Temperature | T [C] | 20, 25, 30, 35, 40 | Stability validation axis |

**Starting Point:** Fix wavelength to white LED and sweep intensity across 5 levels.

This gives 5 x N CRPs with minimal complexity. Expand to multi-wavelength in Phase 2 once the measurement pipeline is validated and baseline metrics are confirmed.

---

## 3. Validation & Test Plan

The test plan consists of five sequential phases. Each phase has explicit pass/fail criteria that must be met before proceeding to the next phase.

**Figure 2: Testing Procedure Flowchart**

Five sequential phases with pass/fail decision gates:

1. Phase 1: Baseline Characterization
2. Phase 2: Bit Extraction and Uniqueness
3. Phase 3: Reliability, BER
4. Phase 4: Temperature Stability, 20 deg C to 40 deg C
5. Phase 5: Randomness

### 3.1 Phase 1: Baseline Characterization

**Goal**

Establish that devices are individually distinct and that measurements are repeatable.

**Procedure**

1. Prepare N >= 20 DSSC devices using the same nominal fabrication process.
2. Place each device in the light isolation box.
3. Apply white LED at 100% intensity as the fixed challenge.
4. Measure full I-V curve using SMU or DIY current-sense circuit.
5. Extract Isc, Voc, FF, Pmax, Rs, and Rsh.
6. Repeat 20 times per device without removing from fixture.
7. Record all raw data.

**Pass Criteria**

- Device-to-device spread in Isc > 3x measurement noise floor
- Within-device repeat CV < 2% for Isc and Voc
- All devices produce statistically distinct I-V signatures

### 3.2 Phase 2: Bit Extraction & Uniqueness

**Bit Extraction Method**

1. Collect Isc values from all N devices under each challenge.
2. Compute population mean across all devices for that challenge.
3. Apply threshold: bit = 1 if Isc_device > mean, else bit = 0.
4. Concatenate bits across challenges to form the PUF response string.

**Uniqueness Metric**

Inter-device Hamming Distance (HD):

```text
HD(Ri, Rj) = (1/n) * SUM(Ri[k] XOR Rj[k]) for k = 1..n
```

Target:

```text
mean HD across all device pairs = 0.50 (+/- 0.05)
```

Interpretation:

- HD approximately 0.50: devices are maximally distinct, ideal PUF
- HD approximately 0.00: devices are nearly identical, PUF failure

**Pass Criteria**

- Mean inter-device HD: 0.45 to 0.55
- Standard deviation of HD distribution < 0.10
- No device pair with HD < 0.20

### 3.3 Phase 3: Reliability

**Procedure**

1. Select 5 representative devices.
2. Enroll each device by recording reference PUF response R_ref.
3. Remove and re-insert device 10 times.
4. Each time, measure and extract new response R_i.
5. Compute intra-device HD between R_ref and each R_i.

**Reliability Metric**

Intra-device BER:

```text
BER = (1/n) * SUM(R_ref[k] XOR R_i[k]) for k = 1..n
```

Target:

```text
BER < 5% pre-ECC
BER < 0.1% post-ECC, using BCH or majority vote
```

**Pass Criteria**

- Mean intra-device BER < 5%
- No single measurement with BER > 15%

### 3.4 Phase 4: Temperature Stability, 20 deg C to 40 deg C

**Procedure**

1. Place device in temperature-controlled enclosure.
2. Measure at T = 20, 25, 30, 35, and 40 deg C.
3. At each temperature, apply all challenges and extract PUF bits.
4. Compare to the 25 deg C reference enrollment.
5. Compute BER vs. temperature.

**Pass Criteria**

- BER vs temperature < 10% across 20 deg C to 40 deg C without compensation
- After linear temperature compensation: BER < 5% across full range

### 3.5 Phase 5: Randomness

| Test | Tool | Checks | Target |
|---|---|---|---|
| Frequency, monobit | NIST SP 800-22, Python | Equal 0s and 1s | p-value > 0.01 |
| Runs test | NIST SP 800-22 | No long identical runs | p-value > 0.01 |
| Min-entropy | Python calculation | Unpredictability per bit | H_min > 0.9 |
| Autocorrelation | numpy/scipy | No adjacent bit correlation | No significant peak |
| Chi-square | scipy.stats | Uniform bit pattern distribution | p-value > 0.01 |

### 3.6 Bit Extraction & Metrics: Visual Summary

The diagram illustrates the four-step process from raw analog measurements through to the key PUF quality metrics.

**Figure 3: Bit Extraction Process and PUF Quality Metrics Visualization**

1. Step 1: Analog response
2. Step 2: Bit extraction
3. Step 3: Uniqueness, HD
4. Step 4: Temperature stability

---

## 4. Lab Setup & Equipment

Two setup tiers are defined: a minimum viable setup to prove PUF behavior, and an enhanced setup for publication-quality data. Both are described below with full block diagrams in the source PDF.

### 4.1 Minimum Viable Setup, Approximately $150 to $300

This setup is sufficient to demonstrate device uniqueness, repeatability, and basic entropy. It uses only commodity components and open-source software.

**Figure 4: Minimum Viable Lab Setup**

Arduino-based data acquisition with LED illumination and isolation box.

| Component | Purpose | Option | Est. Cost |
|---|---|---|---|
| 5W White LED | Primary optical challenge source | High-power LED + heatsink from AliExpress | $5-10 |
| PWM LED driver | Control intensity 10-100% | Arduino PWM output + MOSFET | $3-8 |
| Light isolation box | Eliminate ambient light noise | Black foam board + matte black paint | $10-20 |
| 0.1 Ohm sense resistor | Measure Isc via voltage drop | Precision 0.1% resistor | $2-5 |
| ADS1115 ADC module | 16-bit high-res measurement | I2C module, direct to MCU | $5-10 |
| Arduino / RPi Pico | Data acquisition + PWM control | Arduino Uno or Pi Pico | $5-15 |
| Reference photodiode | Calibrate LED intensity | BPW34 + 1 MOhm resistor | $3-8 |
| Hot plate + thermocouple | Temperature variation | Hot plate + K-type + MAX31855 | $30-60 |
| Pogo pin PCB fixture | Repeatable device contact | DIY PCB with spring pins | $15-30 |
| Laptop / PC | Data logging and analysis | Existing hardware + Python, free | $0 |

### 4.2 Enhanced Setup, Approximately $500 to $2000

Adds precision I-V curve measurement, multi-wavelength optical challenges, transient capture, and precise thermal control for full characterization.

**Figure 5: Enhanced Lab Setup**

SMU-based I-V sweep with RGB LEDs, oscilloscope, and Peltier thermal control.

| Component | Purpose | Option | Est. Cost |
|---|---|---|---|
| Keithley 2400 SMU | Full I-V curve sweep with precision | Used/refurbished; or Keithley 2450 | $300-800 |
| RGB LED array | Multi-wavelength challenges | High-power R/G/B LEDs, 630/530/470 nm, + 3-ch PWM | $30-60 |
| Optical power meter | Absolute intensity calibration | Thorlabs PM100D used, or OPT101 module | $50-200 |
| Rigol DS1054Z oscilloscope | Transient response capture | 4-channel, 50 MHz | $300-400 |
| Peltier + PID controller | Precise thermal control | Peltier module + PID + aluminum block | $80-150 |
| Lock-in amplifier, optional | Low-noise EIS measurements | DIY with STM32 + AD5933 | $100-500 |

### 4.3 Critical Setup Notes

- Light isolation is mandatory; even 1% ambient light contamination degrades reliability.
- Use twisted-pair wiring from device to ADC to minimize EMI pickup.
- Allow 30 seconds thermal settling after each temperature change before measuring.
- Calibrate LED intensity with reference photodiode at the start of every session.
- Log all raw analog values; do not discard data during collection.
- Use the same physical contact pressure each time; pogo pin fixture handles this.

---

## 5. Data Processing Pipeline

### 5.1 Normalization

- Normalize Isc by LED intensity from reference photodiode to remove illumination drift.
- Optionally normalize per-device Isc by its own mean across challenges, as a relative fingerprint.

### 5.2 Bit Extraction Strategies

| Method | How | Best For |
|---|---|---|
| Mean threshold | Bit = 1 if value > population mean for that challenge | Simple; works well with bimodal distribution |
| Median threshold | Bit = 1 if value > population median | More robust to outlier devices |
| Rank-based | Assign bits based on rank ordering of devices | Maximizes uniqueness; inherently balanced |
| Hysteresis band | Only extract bits far from threshold, using a dead-band around mean | Fewer bits but higher reliability |

### 5.3 Error Correction

- Start with majority voting, repeat 3x and take majority; zero hardware cost.
- Graduate to BCH(63,45) or BCH(127,85) codes if BER remains above 2%.
- Use Reed-Solomon for burst errors during temperature sweeps.

---

## 6. Experiment Timeline

| Phase | Duration | Key Deliverable |
|---|---|---|
| Phase 1: Setup & Baseline | 1-2 weeks | Validated setup; baseline I-V curves for all devices |
| Phase 2: Bit Extraction & Uniqueness | 1 week | Inter-device HD plot; HD approximately 0.50 confirmed |
| Phase 3: Reliability | 1 week | Intra-device BER < 5%; enrollment protocol defined |
| Phase 4: Stability, 20-40 C | 1 week | BER vs. temperature curve; compensation model |
| Phase 5: Randomness | 3-5 days | NIST test results; min-entropy estimate |
| Phase 6: Multi-wavelength, optional | 1-2 weeks | Extended CRP space; spectral fingerprint plots |

---

## 7. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Devices too similar, low uniqueness | Medium | Vary fab conditions slightly; add transient response as fingerprint dimension |
| High BER due to contact noise | High | Pogo pin fixture with controlled pressure; average 10+ measurements per challenge |
| Temperature drift causes bit flips | Medium | Per-temperature threshold recalibration; log temperature with every measurement |
| LED intensity drift between sessions | High | Recalibrate against reference photodiode; log intensity with every measurement |
| Dye degradation over time | Medium | Seal devices with UV-resistant encapsulant; track Isc drift as aging metric |

---

## 8. Success Criteria Summary

A DSSC device is confirmed to exhibit strong PUF behavior when all of the following are met:

1. **Uniqueness:** Inter-device Hamming distance = 0.45 to 0.55.
2. **Reliability:** Intra-device BER < 5% pre-ECC and < 0.1% post-ECC.
3. **Randomness:** Min-entropy per bit > 0.9; NIST frequency test p > 0.01.
4. **Stability:** BER < 10% across 20 deg C to 40 deg C without compensation; BER < 5% across 20 deg C to 40 deg C with compensation.

---

## End of Document
