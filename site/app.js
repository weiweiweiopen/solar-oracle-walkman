(async function () {
  const chart = document.querySelector("#iv-chart");
  const summary = document.querySelector("#chart-summary");
  const signatureList = document.querySelector("#signature-list");
  const voiceprint = document.querySelector("#voiceprint");

  try {
    const [curve, voice] = await Promise.all([
      fetchJson("./data/sample_iv_curve.json"),
      fetchJson("./data/sample_7d_voiceprint.json"),
    ]);
    renderChart(curve);
    renderSignature(curve);
    renderVoiceprint(voice);
  } catch (error) {
    if (summary) summary.textContent = `Sample data could not load: ${error.message}`;
  }

  async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${url} returned ${response.status}`);
    return response.json();
  }

  function renderChart(curve) {
    if (!chart) return;
    const voltage = curve.voltage || [];
    const current = curve.current || [];
    const width = 640;
    const height = 360;
    const pad = { left: 64, right: 28, top: 28, bottom: 58 };
    const minV = Math.min(...voltage);
    const maxV = Math.max(...voltage);
    const minI = Math.min(...current);
    const maxI = Math.max(...current);

    const x = (value) => pad.left + ((value - minV) / (maxV - minV || 1)) * (width - pad.left - pad.right);
    const y = (value) => height - pad.bottom - ((value - minI) / (maxI - minI || 1)) * (height - pad.top - pad.bottom);
    const points = voltage.map((v, index) => [x(v), y(current[index])]);
    const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point[0].toFixed(2)} ${point[1].toFixed(2)}`).join(" ");
    const grid = [0, 0.25, 0.5, 0.75, 1]
      .map((step) => {
        const gx = pad.left + step * (width - pad.left - pad.right);
        const gy = pad.top + step * (height - pad.top - pad.bottom);
        return `<line class="grid-line" x1="${gx}" y1="${pad.top}" x2="${gx}" y2="${height - pad.bottom}" />\n<line class="grid-line" x1="${pad.left}" y1="${gy}" x2="${width - pad.right}" y2="${gy}" />`;
      })
      .join("");
    const dots = points
      .map(([cx, cy], index) => `<circle class="curve-dot" cx="${cx.toFixed(2)}" cy="${cy.toFixed(2)}" r="4"><title>${voltage[index].toFixed(2)} V, ${current[index].toExponential(2)} A</title></circle>`)
      .join("");

    chart.innerHTML = `
      ${grid}
      <line class="axis" x1="${pad.left}" y1="${height - pad.bottom}" x2="${width - pad.right}" y2="${height - pad.bottom}" />
      <line class="axis" x1="${pad.left}" y1="${pad.top}" x2="${pad.left}" y2="${height - pad.bottom}" />
      <path class="curve-line" d="${path}" />
      ${dots}
      <text class="chart-label" x="${width / 2 - 42}" y="${height - 16}">Voltage (V)</text>
      <text class="chart-label" x="18" y="${height / 2}" transform="rotate(-90 18 ${height / 2})">Current (A)</text>
      <text class="chart-label" x="${pad.left}" y="24">Isc ${maxI.toExponential(2)} A</text>
      <text class="chart-label" x="${width - 168}" y="${height - pad.bottom - 10}">Voc ${maxV.toFixed(2)} V</text>
    `;

    if (summary) {
      summary.textContent = `${curve.sample_id}: ${voltage.length} points, ${curve.illumination_condition?.source || "stated light source"}, ${curve.illumination_condition?.intensity_w_m2 || "n/a"} W/m2, ${curve.temperature_c} C.`;
    }
  }

  function renderSignature(curve) {
    if (!signatureList) return;
    const rows = [
      ["device_id", curve.device_id],
      ["sample_id", curve.sample_id],
      ["timestamp", curve.timestamp],
      ["illumination", `${curve.illumination_condition?.source || "unknown"}, ${curve.illumination_condition?.intensity_w_m2 || "n/a"} W/m2`],
      ["temperature_c", curve.temperature_c],
      ["claim_boundary", "Measured physical response evidence; not certification or standalone cryptographic identity."],
    ];
    signatureList.innerHTML = rows.map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(String(value))}</dd>`).join("");
  }

  function renderVoiceprint(voice) {
    if (!voiceprint) return;
    voiceprint.innerHTML = voice.features
      .map((value, index) => {
        const label = voice.feature_names[index].replaceAll("_", " ");
        const width = Math.max(4, Math.min(100, value * 100));
        return `<div class="feature-row"><span>${escapeHtml(label)}</span><div class="feature-track"><div class="feature-fill" style="width: ${width}%"></div></div><strong>${value.toFixed(2)}</strong></div>`;
      })
      .join("");
  }

  function escapeHtml(value) {
    return value.replace(/[&<>"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[char]);
  }
})();
