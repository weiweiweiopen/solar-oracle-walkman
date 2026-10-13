#!/usr/bin/env python3
import csv
import datetime as dt
import statistics
import sys
import shutil
from publish_site import disconnected_at
from pathlib import Path

BASE = Path(__file__).resolve().parent
READINGS = BASE / "readings.csv"
SUMMARIES = BASE / "summaries.csv"

end = dt.datetime.now().astimezone()
hours = int(sys.argv[1]) if len(sys.argv) > 1 else 8
start = end - dt.timedelta(hours=hours)

rows = []
if READINGS.exists():
    with READINGS.open(newline="") as f:
        for row in csv.DictReader(f):
            try:
                when = dt.datetime.strptime(row["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
                if start <= when <= end and not disconnected_at(when):
                    rows.append(row)
            except (KeyError, ValueError):
                pass

header = [
    "generated_at", "window_start", "window_end", "samples",
    "voc_mV_min", "voc_mV_mean", "voc_mV_max", "ambient_temp_C_mean",
    "humidity_pct_mean", "pressure_hPa_mean", "lux_mean", "mcu_temp_C_mean",
    "temp_source", "light_source", "light_condition"
]

def valid_values(key, low, high):
    values = []
    for row in rows:
        try:
            value = float(row.get(key, ""))
        except (TypeError, ValueError):
            continue
        if low <= value <= high:
            values.append(value)
    return values


volts = valid_values("voltage_mV", 0, 1200)
temps = valid_values("ambient_temp_C", -20, 80)
humidity = valid_values("humidity_pct", 0, 100)
pressure = valid_values("pressure_hPa", 800, 1100)
lux = valid_values("lux", 0, 200000)
mcu_temps = valid_values("mcu_temp_C", -20, 110)

if volts:
    output = [
        end.isoformat(timespec="seconds"), start.isoformat(timespec="seconds"),
        end.isoformat(timespec="seconds"), str(len(volts)),
        f"{min(volts):.1f}", f"{statistics.fmean(volts):.1f}",
        f"{max(volts):.1f}", f"{statistics.fmean(temps):.2f}" if temps else "",
        f"{statistics.fmean(humidity):.2f}" if humidity else "",
        f"{statistics.fmean(pressure):.2f}" if pressure else "",
        f"{statistics.fmean(lux):.1f}" if lux else "",
        f"{statistics.fmean(mcu_temps):.1f}" if mcu_temps else "",
        rows[-1].get("temp_source", ""), rows[-1].get("light_source", ""),
        rows[-1].get("light_condition", "")
    ]
else:
    output = [end.isoformat(timespec="seconds"), start.isoformat(timespec="seconds"),
              end.isoformat(timespec="seconds"), "0", "", "", "", "", "", "", "", "", "", "", ""]

new_file = not SUMMARIES.exists() or SUMMARIES.stat().st_size == 0
if not new_file:
    with SUMMARIES.open(newline="") as f:
        current_header = next(csv.reader(f), [])
    if current_header != header:
        stamp = end.strftime("%Y%m%d-%H%M%S")
        shutil.move(SUMMARIES, BASE / f"summaries-legacy-{stamp}.csv")
        new_file = True
with SUMMARIES.open("a", newline="") as f:
    writer = csv.writer(f)
    if new_file:
        writer.writerow(header)
    writer.writerow(output)

if volts:
    environment = []
    if temps:
        environment.append(f"環境溫度 {statistics.fmean(temps):.2f} °C")
    if humidity:
        environment.append(f"濕度 {statistics.fmean(humidity):.1f}%")
    if pressure:
        environment.append(f"氣壓 {statistics.fmean(pressure):.2f} hPa")
    if lux:
        environment.append(f"光照 {statistics.fmean(lux):.1f} lux")
    print(
        f"DSSC Voc 時段摘要（{start:%m/%d %H:%M}–{end:%H:%M}）："
        f"{len(volts)} 筆有效電壓，平均 {statistics.fmean(volts):.1f} mV，"
        f"範圍 {min(volts):.1f}–{max(volts):.1f} mV"
        + ("；" + "，".join(environment) if environment else "")
        + "。"
    )
else:
    print(f"DSSC Voc 時段摘要（{start:%m/%d %H:%M}–{end:%H:%M}）：沒有有效資料，請檢查 ESP32 與 Wi-Fi 連線。")
