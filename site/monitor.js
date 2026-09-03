(function () {
  const DEVICE = "green_proofs_are_not_always_about_tax_write-offs_1";
  const DATA_ROOT = `./data/${DEVICE}`;
  const GAP_MS = 12.5 * 60 * 1000;
  const NS = "http://www.w3.org/2000/svg";

  const root = document.querySelector("#material-monitor");
  if (!root) return;

  fetch(`${DATA_ROOT}/status.json?v=${Date.now()}`, { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error(`status ${response.status}`);
      return response.json();
    })
    .then(renderMonitor)
    .catch(() => {
      setText("[data-monitor-reading]", "The first daily view is still on its way.");
      root.classList.add("material-monitor--waiting");
    });

  function renderMonitor(status) {
    renderTable(status);
    renderRetention(status);
    renderVoc(status.recent || []);
    renderLux(status.recent || []);
    renderConditions(status.recent || []);
  }

  function renderTable(status) {
    const latest = status.latest;
    const table = root.querySelector("[data-monitor-table]");
    if (!latest || !table) return;
    const rows = [
      ["Observed", formatDateTime(latest.timestamp)],
      ["Open-circuit voltage", format(latest.voltage_mV, 1, "mV")],
      ["Ambient temperature", format(latest.ambient_temp_C, 2, "°C")],
      ["Relative humidity", format(latest.humidity_pct, 2, "%")],
      ["Air pressure", format(latest.pressure_hPa, 2, "hPa")],
      ["Illuminance", format(latest.lux, 1, "lux")],
      [
        "Continuity at publication",
        status.snapshot_state === "continuous" ? "continuous" : "interrupted",
      ],
    ];
    table.replaceChildren(
      ...rows.map(([label, value]) => {
        const tr = document.createElement("tr");
        const th = document.createElement("th");
        const td = document.createElement("td");
        th.scope = "row";
        th.textContent = label;
        td.textContent = value;
        tr.append(th, td);
        return tr;
      })
    );
    setText(
      "[data-monitor-reading]",
      `${format(latest.voltage_mV, 1, "mV")} under ${format(latest.lux, 1, "lux")} · ${formatDateTime(latest.timestamp)}`
    );
    setText(
      "[data-monitor-updated]",
      `Daily view published ${formatDateTime(status.generated_at)} · ${status.valid_sample_count} included / ${status.invalid_sample_count} excluded`
    );
    const completeDays = Number(status.complete_comparable_days || 0);
    const slope = status.theil_sen_slope_pct_per_day;
    setText(
      "[data-monitor-trend]",
      slope == null
        ? `collecting comparable days · ${completeDays}/7`
        : `${slope >= 0 ? "+" : ""}${Number(slope).toFixed(3)}% / day`
    );
  }

  function renderRetention(status) {
    const host = root.querySelector('[data-monitor-chart="retention"]');
    if (!host) return;
    const daily = (status.daily || [])
      .filter((row) => row.retention_pct != null)
      .map((row) => ({ ...row, time: dateAtNoon(row.date) }));
    if (!daily.length) return renderEmpty(host, "Waiting for comparable light and temperature.");

    const width = 1000;
    const height = 360;
    const pad = { left: 74, right: 28, top: 26, bottom: 48 };
    const xs = daily.map((row) => row.time);
    const ys = daily.flatMap((row) => [
      Number(row.retention_pct),
      numberOrNull(row.retention_ci_low_pct),
      numberOrNull(row.retention_ci_high_pct),
    ]).filter(Number.isFinite);
    const xDomain = paddedTimeDomain(xs);
    const minY = Math.min(100, ...ys);
    const maxY = Math.max(100, ...ys);
    const margin = Math.max(3, (maxY - minY) * 0.2);
    const yDomain = [Math.floor(minY - margin), Math.ceil(maxY + margin)];
    const sx = scale(xDomain, [pad.left, width - pad.right]);
    const sy = scale(yDomain, [height - pad.bottom, pad.top]);
    const svg = chartSvg(width, height, "Daily voltage retention under comparable conditions");
    drawGrid(svg, { width, height, pad, yDomain, sy, unit: "%" });

    svg.append(svgEl("line", {
      x1: pad.left,
      y1: sy(100),
      x2: width - pad.right,
      y2: sy(100),
      class: "monitor-reference-line",
    }));
    svg.append(svgText(pad.left + 8, sy(100) - 8, "100% BASELINE", "monitor-reference-label"));

    const dailyPath = linePath(daily, (row) => sx(row.time), (row) => sy(row.retention_pct), Infinity);
    svg.append(svgEl("path", { d: dailyPath, class: "monitor-line monitor-line--daily" }));

    daily.forEach((row) => {
      if (row.retention_ci_low_pct != null && row.retention_ci_high_pct != null) {
        const x = sx(row.time);
        const low = sy(row.retention_ci_low_pct);
        const high = sy(row.retention_ci_high_pct);
        svg.append(
          svgEl("line", { x1: x, y1: low, x2: x, y2: high, class: "monitor-ci" }),
          svgEl("line", { x1: x - 6, y1: low, x2: x + 6, y2: low, class: "monitor-ci" }),
          svgEl("line", { x1: x - 6, y1: high, x2: x + 6, y2: high, class: "monitor-ci" })
        );
      }
      svg.append(svgEl("circle", {
        cx: sx(row.time),
        cy: sy(row.retention_pct),
        r: row.quality === "complete" ? 5 : 6,
        class: row.quality === "complete" ? "monitor-point" : "monitor-point monitor-point--partial",
      }));
    });

    const moving = daily.filter((row) => row.moving_7d_median_pct != null);
    if (moving.length > 1) {
      svg.append(svgEl("path", {
        d: linePath(moving, (row) => sx(row.time), (row) => sy(row.moving_7d_median_pct), Infinity),
        class: "monitor-line monitor-line--median",
      }));
    }

    const slope = numberOrNull(status.theil_sen_slope_pct_per_day);
    const complete = daily.filter((row) => row.quality === "complete");
    if (slope != null && complete.length >= 2) {
      const origin = complete[0].time;
      const intercepts = complete.map((row) => row.retention_pct - slope * ((row.time - origin) / 86400000));
      const intercept = median(intercepts);
      const start = complete[0].time;
      const end = complete[complete.length - 1].time;
      const startY = intercept + slope * ((start - origin) / 86400000);
      const endY = intercept + slope * ((end - origin) / 86400000);
      svg.append(svgEl("line", {
        x1: sx(start), y1: sy(startY), x2: sx(end), y2: sy(endY), class: "monitor-trend-line",
      }));
    } else {
      svg.append(svgText(
        width - pad.right,
        pad.top + 18,
        `COLLECTING COMPARABLE DAYS · ${complete.length}/7`,
        "monitor-collecting-label",
        "end"
      ));
    }
    drawTimeLabels(svg, xDomain, sx, height, pad);
    host.replaceChildren(svg);
  }

  function renderVoc(recent) {
    const host = root.querySelector('[data-monitor-chart="voc"]');
    if (!host) return;
    const rows = validRecent(recent, "voltage_mV");
    if (!rows.length) return renderEmpty(host, "No comparable observations yet.");
    const hourly = aggregateHourly(rows, "voltage_mV");
    renderSeriesChart(host, {
      rows,
      values: (row) => row.voltage_mV,
      transform: (value) => value,
      unit: "mV",
      label: "Open-circuit voltage",
      overlay: hourly,
      overlayValues: (row) => row.value,
    });
  }

  function renderLux(recent) {
    const host = root.querySelector('[data-monitor-chart="lux"]');
    if (!host) return;
    const rows = validRecent(recent, "lux").filter((row) => row.lux >= 0);
    if (!rows.length) return renderEmpty(host, "No comparable observations yet.");
    renderSeriesChart(host, {
      rows,
      values: (row) => row.lux,
      transform: (value) => Math.log10(value + 1),
      tickFormat: (value) => `${Math.round(Math.pow(10, value) - 1)}`,
      unit: "lux",
      label: "Illuminance on a logarithmic scale",
    });
  }

  function renderConditions(recent) {
    const host = root.querySelector('[data-monitor-chart="conditions"]');
    if (!host) return;
    const rows = (recent || [])
      .filter((row) => row.valid)
      .map((row) => ({ ...row, time: Date.parse(row.timestamp) }))
      .filter((row) => Number.isFinite(row.time));
    if (!rows.length) return renderEmpty(host, "No comparable observations yet.");

    const width = 1000;
    const height = 300;
    const pad = { left: 74, right: 28, top: 20, bottom: 42 };
    const gap = 34;
    const panelHeight = (height - pad.top - pad.bottom - gap) / 2;
    const xDomain = paddedTimeDomain(rows.map((row) => row.time));
    const sx = scale(xDomain, [pad.left, width - pad.right]);
    const svg = chartSvg(width, height, "Ambient temperature and relative humidity in aligned panels");
    [
      { key: "ambient_temp_C", label: "°C", top: pad.top, className: "monitor-line--condition" },
      { key: "humidity_pct", label: "% RH", top: pad.top + panelHeight + gap, className: "monitor-line--humidity" },
    ].forEach((series) => {
      const values = rows.map((row) => row[series.key]).filter(Number.isFinite);
      const yDomain = paddedNumericDomain(values);
      const sy = scale(yDomain, [series.top + panelHeight, series.top]);
      svg.append(
        svgEl("line", { x1: pad.left, y1: series.top + panelHeight, x2: width - pad.right, y2: series.top + panelHeight, class: "monitor-axis" }),
        svgText(pad.left - 10, series.top + 10, `${formatTick(yDomain[1])} ${series.label}`, "monitor-axis-label", "end"),
        svgText(pad.left - 10, series.top + panelHeight, `${formatTick(yDomain[0])}`, "monitor-axis-label", "end"),
        svgEl("path", {
          d: linePath(rows, (row) => sx(row.time), (row) => sy(row[series.key]), GAP_MS),
          class: `monitor-line ${series.className}`,
        })
      );
    });
    drawTimeLabels(svg, xDomain, sx, height, pad);
    host.replaceChildren(svg);
  }

  function renderSeriesChart(host, options) {
    const width = 1000;
    const height = 270;
    const pad = { left: 74, right: 28, top: 20, bottom: 42 };
    const transformed = options.rows.map((row) => options.transform(options.values(row)));
    const xDomain = paddedTimeDomain(options.rows.map((row) => row.time));
    const yDomain = paddedNumericDomain(transformed);
    const sx = scale(xDomain, [pad.left, width - pad.right]);
    const sy = scale(yDomain, [height - pad.bottom, pad.top]);
    const svg = chartSvg(width, height, options.label);
    drawGrid(svg, {
      width,
      height,
      pad,
      yDomain,
      sy,
      unit: options.unit,
      tickFormat: options.tickFormat,
    });
    svg.append(svgEl("path", {
      d: linePath(
        options.rows,
        (row) => sx(row.time),
        (row) => sy(options.transform(options.values(row))),
        GAP_MS
      ),
      class: "monitor-line monitor-line--raw",
    }));
    if (options.overlay && options.overlay.length > 1) {
      svg.append(svgEl("path", {
        d: linePath(
          options.overlay,
          (row) => sx(row.time),
          (row) => sy(options.transform(options.overlayValues(row))),
          GAP_MS * 5
        ),
        class: "monitor-line monitor-line--hourly",
      }));
    }
    drawTimeLabels(svg, xDomain, sx, height, pad);
    host.replaceChildren(svg);
  }

  function validRecent(recent, key) {
    return (recent || [])
      .filter((row) => row.valid && Number.isFinite(Number(row[key])))
      .map((row) => ({ ...row, [key]: Number(row[key]), time: Date.parse(row.timestamp) }))
      .filter((row) => Number.isFinite(row.time));
  }

  function aggregateHourly(rows, key) {
    const groups = new Map();
    rows.forEach((row) => {
      const hour = Math.floor(row.time / 3600000) * 3600000;
      if (!groups.has(hour)) groups.set(hour, []);
      groups.get(hour).push(row);
    });
    return Array.from(groups, ([, samples]) => ({
      time: median(samples.map((row) => row.time)),
      value: median(samples.map((row) => row[key])),
    })).sort((a, b) => a.time - b.time);
  }

  function linePath(rows, x, y, maxGap) {
    let previous = null;
    return rows.map((row) => {
      const command = previous == null || row.time - previous > maxGap ? "M" : "L";
      previous = row.time;
      return `${command}${x(row).toFixed(2)} ${y(row).toFixed(2)}`;
    }).join(" ");
  }

  function drawGrid(svg, { width, height, pad, yDomain, sy, unit, tickFormat }) {
    const formatter = tickFormat || formatTick;
    for (let index = 0; index <= 4; index += 1) {
      const value = yDomain[0] + ((yDomain[1] - yDomain[0]) * index) / 4;
      const y = sy(value);
      svg.append(
        svgEl("line", { x1: pad.left, y1: y, x2: width - pad.right, y2: y, class: "monitor-grid-line" }),
        svgText(pad.left - 10, y + 4, `${formatter(value)}${index === 4 ? ` ${unit}` : ""}`, "monitor-axis-label", "end")
      );
    }
    svg.append(
      svgEl("line", { x1: pad.left, y1: pad.top, x2: pad.left, y2: height - pad.bottom, class: "monitor-axis" }),
      svgEl("line", { x1: pad.left, y1: height - pad.bottom, x2: width - pad.right, y2: height - pad.bottom, class: "monitor-axis" })
    );
  }

  function drawTimeLabels(svg, domain, sx, height, pad) {
    const start = domain[0];
    const end = domain[1];
    svg.append(
      svgText(sx(start), height - 14, formatShortDate(start), "monitor-axis-label", "start"),
      svgText(sx(end), height - 14, formatShortDate(end), "monitor-axis-label", "end")
    );
  }

  function chartSvg(width, height, title) {
    const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", class: "monitor-svg" });
    const titleEl = svgEl("title");
    titleEl.textContent = title;
    svg.append(titleEl);
    return svg;
  }

  function renderEmpty(host, message) {
    const paragraph = document.createElement("p");
    paragraph.className = "material-chart__empty";
    paragraph.textContent = message;
    host.replaceChildren(paragraph);
  }

  function scale(domain, range) {
    const span = domain[1] - domain[0] || 1;
    return (value) => range[0] + ((value - domain[0]) / span) * (range[1] - range[0]);
  }

  function paddedTimeDomain(values) {
    const min = Math.min(...values);
    const max = Math.max(...values);
    const pad = min === max ? 12 * 3600000 : Math.max(30 * 60000, (max - min) * 0.025);
    return [min - pad, max + pad];
  }

  function paddedNumericDomain(values) {
    const min = Math.min(...values);
    const max = Math.max(...values);
    const pad = min === max ? Math.max(1, Math.abs(min) * 0.05) : (max - min) * 0.12;
    return [min - pad, max + pad];
  }

  function dateAtNoon(value) {
    return Date.parse(`${value}T12:00:00+08:00`);
  }

  function format(value, digits, unit) {
    return Number.isFinite(Number(value)) ? `${Number(value).toFixed(digits)} ${unit}` : "—";
  }

  function formatTick(value) {
    const span = Math.abs(value);
    if (span < 10) return value.toFixed(1);
    return value.toFixed(0);
  }

  function formatDateTime(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Taipei",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(date);
  }

  function formatShortDate(value) {
    return new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Taipei",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(new Date(value));
  }

  function median(values) {
    const ordered = values.filter(Number.isFinite).slice().sort((a, b) => a - b);
    if (!ordered.length) return null;
    const middle = Math.floor(ordered.length / 2);
    return ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2;
  }

  function numberOrNull(value) {
    return value == null || value === "" ? null : Number(value);
  }

  function svgEl(name, attributes = {}) {
    const element = document.createElementNS(NS, name);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
    return element;
  }

  function svgText(x, y, content, className, anchor) {
    const text = svgEl("text", { x, y, class: className });
    if (anchor) text.setAttribute("text-anchor", anchor);
    text.textContent = content;
    return text;
  }

  function setText(selector, value) {
    const element = root.querySelector(selector);
    if (element) element.textContent = value;
  }
})();
