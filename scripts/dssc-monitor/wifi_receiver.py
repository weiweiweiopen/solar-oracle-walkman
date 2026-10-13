#!/usr/bin/env python3
import csv
import fcntl
import json
import math
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOG = BASE / "readings.csv"
STATUS_LOG = BASE / "device_status.jsonl"
B_LOG = BASE / "readings-b.csv"
DEVICE_ID = "esp32c3-64e833b913b8"
SAMPLE_A = "green_proofs_are_not_always_about_tax_write-offs_1"
SAMPLE_B = "dssc_55x55_b"
TOKEN = None  # Loaded only by the service entry point.
HEADER = ["timestamp", "raw", "voltage_mV", "voltage_V", "ambient_temp_C",
          "humidity_pct", "pressure_hPa", "lux", "mcu_temp_C", "temp_source",
          "light_source", "light_condition"]
FIELDS = HEADER[1:9]
STATUS_FIELDS = ["boot_id", "report_sequence", "uptime_s", "reset_reason",
                 "restart_marker", "wifi_rssi_dBm", "wifi_attempts",
                 "last_disconnect_reason", "previous_http_code", "free_heap_B",
                 "prior_disconnect_reason", "prior_http_code", "prior_rssi_dBm",
                 "prior_uptime_s", "prior_wifi_attempts"]
WRITE_LOCK = threading.Lock()


def load_last_event_key():
    if not STATUS_LOG.exists():
        return None
    last_key = None
    try:
        with STATUS_LOG.open() as f:
            for line in f:
                try:
                    item = json.loads(line)
                    if item.get("boot_id") is not None and item.get("report_sequence") is not None:
                        last_key = (str(item["boot_id"]), str(item["report_sequence"]))
                except (json.JSONDecodeError, TypeError):
                    continue
    except OSError:
        return None
    return last_key


LAST_EVENT_KEY = load_last_event_key()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok\n")
        else:
            self.send_error(404)

    def do_POST(self):
        global LAST_EVENT_KEY
        if self.path != "/readings" or self.headers.get("X-DSSC-Token") != TOKEN:
            self.send_error(403); return
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n < 2 or n > 4096: raise ValueError("bad length")
            data = json.loads(self.rfile.read(n))
            if not isinstance(data, dict): raise ValueError("expected object")
            channels = data.get("channels", [])
            b_reading = None
            if "schema_version" in data or channels or "sample_id" in data:
                if (data.get("schema_version") != 2 or data.get("device_id") != DEVICE_ID
                        or data.get("sample_id") != SAMPLE_A or data.get("gpio") != 3):
                    raise ValueError("unknown device / A mapping")
                if not isinstance(channels, list) or len(channels) != 1:
                    raise ValueError("expected one B channel")
                b_reading = channels[0]
                if (not isinstance(b_reading, dict) or b_reading.get("sample_id") != SAMPLE_B
                        or b_reading.get("gpio") != 2):
                    raise ValueError("unknown B mapping")
                for key in ("raw", "voltage_mV", "voltage_V"):
                    if (type(b_reading.get(key)) not in (int, float)
                            or not math.isfinite(b_reading[key])):
                        raise ValueError("invalid B reading")
            values = [data[k] for k in FIELDS]
            row = [datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"), *values,
                   "sht20", "bh1750", "fixed_position_sensor_facing_light"]
            status = {"received_at": row[0], "remote_ip": self.client_address[0]}
            status.update({key: data.get(key) for key in STATUS_FIELDS})
            status.update(device_id=DEVICE_ID, sample_id=SAMPLE_A, gpio=3,
                          channels=[{"sample_id": SAMPLE_B, "gpio": 2}] if b_reading else [])
            event_key = None
            if data.get("boot_id") is not None and data.get("report_sequence") is not None:
                event_key = (str(data["boot_id"]), str(data["report_sequence"]))

            with WRITE_LOCK:
                if event_key is None or event_key != LAST_EVENT_KEY:
                    with LOG.open("a+", newline="") as f:
                        fcntl.flock(f, fcntl.LOCK_EX)
                        f.seek(0, 2)
                        if f.tell() == 0: csv.writer(f).writerow(HEADER)
                        csv.writer(f).writerow(row)
                        f.flush()
                        fcntl.flock(f, fcntl.LOCK_UN)
                    if b_reading is not None:
                        b_values = dict(data, **b_reading)
                        b_row = [row[0], *[b_values[k] for k in FIELDS], *row[9:]]
                        with B_LOG.open("a+", newline="") as f:
                            fcntl.flock(f, fcntl.LOCK_EX)
                            f.seek(0, 2)
                            if f.tell() == 0: csv.writer(f).writerow(HEADER)
                            csv.writer(f).writerow(b_row)
                            f.flush()
                            fcntl.flock(f, fcntl.LOCK_UN)
                    try:
                        with STATUS_LOG.open("a+") as f:
                            fcntl.flock(f, fcntl.LOCK_EX)
                            f.write(json.dumps(status, separators=(",", ":")) + "\n")
                            f.flush()
                            fcntl.flock(f, fcntl.LOCK_UN)
                    except OSError as e:
                        print(f"diagnostic log write failed: {e}", file=sys.stderr, flush=True)
                    if event_key is not None:
                        LAST_EVENT_KEY = event_key
            self.send_response(204); self.end_headers()
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            self.send_error(400, str(e))
        except OSError as e:
            self.send_error(500, str(e))

    def log_message(self, fmt, *args):
        try:
            with (BASE / "wifi_receiver.log").open("a") as f:
                f.write(f"{datetime.now().astimezone().isoformat()} {fmt % args}\n")
        except OSError as e:
            print(f"request log write failed: {e}", file=sys.stderr, flush=True)

if __name__ == "__main__":
    TOKEN = (BASE / ".wifi_token").read_text().strip()
    if not TOKEN: raise RuntimeError("Missing receiver credential")
    ThreadingHTTPServer(("0.0.0.0", 8787), Handler).serve_forever()
