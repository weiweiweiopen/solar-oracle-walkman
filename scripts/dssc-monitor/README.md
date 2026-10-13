# DSSC dual-channel monitor

## Active path (2026-10-13)

`firmware/src/main.cpp` + `firmware/platformio.ini` is the running Wi-Fi firmware.
`firmware/dssc_wifi/dssc_wifi.ino` is an older BLE sketch, **not** the active build.
Read-only chip identification confirmed ESP32-C3 QFN32 revision v0.4, 4 MB flash.
The USB port at implementation was `/dev/cu.usbmodem21201`; inspect `lsof` before opening it (opening/resetting can interrupt acquisition).

| Sample | Stable sample_id | GPIO | Local raw CSV |
|---|---|---:|---|
| DSSC 55x55 A | green_proofs_are_not_always_about_tax_write-offs_1 | 3 | readings.csv |
| DSSC 55x55 B | dssc_55x55_b | 2 | readings-b.csv |

Physical device_id is `esp32c3-64e833b913b8`. GPIO2 and GPIO3 are C3 ADC1 inputs. Both use the original 12-bit resolution, ADC_2_5db attenuation, 64-sample analogRead/analogReadMilliVolts averaging, 5-minute cadence, no new divider multiplier, no output/load control. I2C pins 8/9 and environmental sensors are unchanged and shared. Preserve the original 0–1200 mV publication validity bound. A plausible ADC reading does **not** establish wiring safety, insulation, connection quality, or the maximum possible open-circuit voltage. No independent physical voltage measurement was available.

## Quality policy and raw provenance

`channels.json` is the date-granularity user-report quality overlay. User reported on 2026-10-13 that A was unplugged from 2026-10-03 through 2026-10-13 and its readings were noise. All Asia/Taipei dates from 2026-10-03 onward are conservatively excluded until a confirmed reconnection timestamp is supplied. This is **not** a claim that unplugging occurred exactly at midnight. `confirmed_reconnected_at: null` means no recovery has been confirmed. Do not infer recovery from voltage, firmware reset, or Wi-Fi uptime. Preserve this report when adding future recovery evidence; never infer or backdate an exact time.

A's local raw history is append-only and unchanged. Public readings preserve original numeric fields and add sample/device/GPIO plus `quality=excluded` and `quality_reason=sensor_disconnected_invalid_measurement`. Invalid readings do not contribute to baseline, retention, trend, summary voltage, or curves. All-invalid dates have zero valid-sample count and null voltage/retention (not fabricated zero voltage). Chart paths break over invalid observations and missing days. These are Voc observations, not power/energy-generation measurements.

B starts only at its actual first received GPIO2 acquisition; no synthetic/backfilled history. Range-valid B readings rely on the user's report of connection, not automatic physical-connection detection. Status explicitly carries `user_reported_connected` provenance; freshness is separately reported as continuous/interrupted. If B is unplugged later, add a quality report rather than assuming low/noisy voltage is valid.

## Collector and schema

`com.wisemouse.dssc-wifi-receiver` runs `wifi_receiver.py` on port 8787; `GET /health` is read-only. `POST /readings` remains authenticated. Keep `.wifi_token` local/private. Legacy payloads map only to A. Schema 2 keeps A voltage at the top level and adds exactly one B entry in `channels`; receiver checks device_id/sample_id/GPIO and never routes B to A. Environment values are shared. Dedup uses the existing boot_id/report_sequence event key for the combined report. The CSV files are independently locked and written; a process crash between the two appends is not a transaction (inspect status/raw records before retry repair). No serial collector was loaded during this migration.

## Build / recovery

Use the existing `.venv/bin/platformio run` in `firmware/`. Secrets belong only in ignored `firmware/src/wifi_secrets.h` with WIFI_SSID, WIFI_PASSWORD and TOKEN declarations, configured through a private local editor; do not place them in commands/chat/public Git. Public source is credential-free; build outputs and full flash backups contain secrets and must remain private.

Before flash: inspect USB ownership and exact chip, save current source/config and full flash, inspect partition table, ensure a recoverable app. For this board, app0 is at 0x10000, size 0x140000; NVS is 0x9000–0xdfff. This migration wrote **only** the application at 0x10000 and esptool verified its hash. Do not erase all flash. For rollback, stop any serial reader, write the privately backed-up prior firmware.bin to the verified app0 offset using esptool, then verify Wi-Fi collector health and a real report. Do not write a full-flash backup unless recovery explicitly requires it. Retain the invalid-data policy even if firmware is rolled back.

Local private backup/evidence: `../artifacts/dssc-dual-monitor-20261013/` (full flash and former source/config under private-backup). Operations are timestamped in operations.jsonl. The receiver stays running during USB flash; only its own LaunchAgent is restarted for receiver code changes. Health-check immediately after restarting. No global OpenClaw configuration changes.

## Publication

`com.wisemouse.dssc-site-publisher` runs `publish_site.py --push` using the clean canonical checkout `../github-automation/solar-oracle-walkman`. It snapshots both channels to `site/data/<sample_id>/`, then commits only those generated files and `site/data/channels.json`. Dirty-check prevents mixing unrelated changes; no force push. Do not edit the other similarly named staging/reference repos. Website is https://weiweiweiopen.github.io/solar-oracle-walkman/ . Existing GitHub Pages workflow publishes `site/` on main push; snapshots remain daily, not a live browser stream.

The public repository's `scripts/dssc-monitor/` is a credential-free versioned copy of the deployed code/config. Deploy edits deliberately to this local service directory; copies alone do not restart the service. Test with `python3 test_dual.py` in that versioned directory (tests use temporary CSVs and a loopback ephemeral server, never production measurements).
