/* CS Conference Explorer — interactive acceptance-rate charts.
   Data: ../csconferences.csv (Area,Conference,Year,Sequence,Accepted,Submitted,Source,Notes).
   Multi-cycle years (Sequence > 1) are summed per conference-year. */
(function () {
  "use strict";

  const AREA_NAMES = {
    AI: "Artificial intelligence", Vision: "Computer vision", ML: "Machine learning",
    NLP: "Natural language processing", "Web+IR": "Web & information retrieval",
    Arch: "Computer architecture", Networks: "Computer networks", Security: "Computer security",
    DB: "Databases", Metrics: "Measurement & perf. analysis", Mobile: "Mobile computing",
    OS: "Operating systems", PL: "Programming languages", SE: "Software engineering",
    Theory: "Algorithms & complexity", Logic: "Logic & verification", Crypt: "Cryptography",
    Graphics: "Computer graphics", HCI: "Human-computer interaction",
    Bed: "Embedded & real-time systems", ECom: "Economics & computation", Robotics: "Robotics",
  };
  // CSrankings super-area groupings (src/config.ts)
  const SUPER = {
    AI: "AI", Vision: "AI", ML: "AI", NLP: "AI", "Web+IR": "AI",
    Arch: "Systems", Networks: "Systems", Security: "Systems", DB: "Systems", Metrics: "Systems",
    Mobile: "Systems", OS: "Systems", PL: "Systems", SE: "Systems", Bed: "Systems",
    Theory: "Theory", Logic: "Theory", Crypt: "Theory",
    Graphics: "Interdisciplinary", HCI: "Interdisciplinary", ECom: "Interdisciplinary", Robotics: "Interdisciplinary",
  };
  const SUPER_VAR = { AI: "--area-ai", Systems: "--area-systems", Theory: "--area-theory", Interdisciplinary: "--area-inter" };
  const SUPER_SHAPE = { AI: d3.symbolCircle, Systems: d3.symbolSquare, Theory: d3.symbolTriangle, Interdisciplinary: d3.symbolDiamond };
  const MAX_SELECTED = 8;

  const state = {
    supers: new Set(["AI", "Systems", "Theory", "Interdisciplinary"]),
    from: null, to: null, search: "",
    selected: [],          // conference names, in selection order
    slotOf: new Map(),     // conference -> color slot (1..8); sticky while selected
    sortKey: "rate", sortDir: 1,
    logSubs: true,
  };

  const fmtPct = d3.format(".1%");
  const fmtInt = d3.format(",");
  const css = (name) => getComputedStyle(document.querySelector(".viz-root")).getPropertyValue(name).trim();
  const tip = document.getElementById("tooltip");

  let byConf = new Map();   // conf -> {conf, area, super, years:[{year,accepted,submitted,rate,rows}]}
  let allYears = [];

  d3.text("../csconferences.csv").then((text) => {
    const rows = d3.csvParse(text);
    const grouped = d3.group(rows, (r) => r.Conference);
    for (const [conf, rs] of grouped) {
      const area = rs[0].Area;
      const years = Array.from(d3.group(rs, (r) => +r.Year), ([year, yr]) => {
        const accepted = d3.sum(yr, (r) => +r.Accepted);
        const submitted = d3.sum(yr, (r) => +r.Submitted);
        return { year, accepted, submitted, rate: submitted ? accepted / submitted : NaN, rows: yr };
      }).filter((d) => d.submitted > 0 && isFinite(d.rate)).sort((a, b) => a.year - b.year);
      if (years.length) byConf.set(conf, { conf, area, areaName: AREA_NAMES[area] || area, super: SUPER[area] || "Systems", years });
    }
    allYears = d3.range(d3.min(rows, (r) => +r.Year), d3.max(rows, (r) => +r.Year) + 1);
    readHash();
    setupControls();
    render();
    window.addEventListener("resize", debounce(renderCharts, 150));
  }).catch((err) => {
    document.querySelector("main").insertAdjacentHTML("afterbegin",
      `<div class="panel"><p class="empty">Could not load data (${err.message}). If viewing locally, serve the repository root over HTTP.</p></div>`);
  });

  // ---------- state <-> URL ----------
  function readHash() {
    const p = new URLSearchParams(location.hash.slice(1));
    const c = p.get("c");
    if (c) for (const name of c.split(",")) if (byConf.has(name)) addSelected(name, false);
    if (p.get("from")) state.from = +p.get("from");
    if (p.get("to")) state.to = +p.get("to");
    if (p.get("areas")) state.supers = new Set(p.get("areas").split(",").filter((s) => SUPER_VAR[s]));
    if (!state.selected.length) for (const name of ["ICLR", "NeurIPS", "SOSP", "PLDI", "STOC"]) if (byConf.has(name)) addSelected(name, false);
  }
  function writeHash() {
    const p = new URLSearchParams();
    if (state.selected.length) p.set("c", state.selected.join(","));
    if (state.from !== allYears[0] + 0 && state.from) p.set("from", state.from);
    if (state.to !== allYears[allYears.length - 1] && state.to) p.set("to", state.to);
    if (state.supers.size < 4) p.set("areas", [...state.supers].join(","));
    // absolute path: a <base href="explore/"> (homepage mode) must not redirect the URL into /explore/
    history.replaceState(null, "", location.pathname + location.search + "#" + p.toString().replace(/%2C/g, ","));
  }

  function addSelected(conf, rerender = true) {
    if (state.selected.includes(conf)) return;
    if (state.selected.length >= MAX_SELECTED) { flashHint(`Up to ${MAX_SELECTED} conferences can be compared — remove one first.`); return; }
    const used = new Set(state.selected.map((c) => state.slotOf.get(c)));
    const slot = d3.range(1, MAX_SELECTED + 1).find((s) => !used.has(s));
    state.slotOf.set(conf, slot);
    state.selected.push(conf);
    if (rerender) render();
  }
  function removeSelected(conf) {
    state.selected = state.selected.filter((c) => c !== conf);
    state.slotOf.delete(conf);
    render();
  }
  function toggleSelected(conf) { state.selected.includes(conf) ? removeSelected(conf) : addSelected(conf); }
  const seriesColor = (conf) => css(`--series-${state.slotOf.get(conf)}`);
  const areaColor = (sup) => css(SUPER_VAR[sup]);

  function flashHint(msg) {
    const h = document.getElementById("compare-hint");
    h.textContent = msg; h.style.color = "var(--text-primary)";
    setTimeout(() => { h.style.color = ""; updateHint(); }, 2500);
  }
  function updateHint() {
    document.getElementById("compare-hint").textContent = state.selected.length
      ? "Hover the charts for exact values. Click table rows or scatter points to add or remove conferences."
      : "Click conferences in the table or the scatter plot to add them (up to 8).";
  }

  // ---------- controls ----------
  function setupControls() {
    const yf = d3.select("#year-from"), yt = d3.select("#year-to");
    for (const sel of [yf, yt]) sel.selectAll("option").data(allYears).join("option").attr("value", (d) => d).text((d) => d);
    if (!state.from) state.from = 2000;
    if (!state.to) state.to = allYears[allYears.length - 1];
    yf.property("value", state.from).on("change", function () { state.from = +this.value; if (state.from > state.to) { state.to = state.from; yt.property("value", state.to); } render(); });
    yt.property("value", state.to).on("change", function () { state.to = +this.value; if (state.to < state.from) { state.from = state.to; yf.property("value", state.from); } render(); });

    d3.selectAll(".area-pill").each(function () { this.setAttribute("aria-pressed", state.supers.has(this.dataset.super)); })
      .on("click", function () {
        const s = this.dataset.super;
        state.supers.has(s) ? state.supers.delete(s) : state.supers.add(s);
        this.setAttribute("aria-pressed", state.supers.has(s));
        render();
      });
    d3.select("#search").on("input", function () { state.search = this.value.trim().toLowerCase(); render(); });
    d3.select("#log-subs").on("change", function () { state.logSubs = this.checked; renderCharts(); });
    d3.selectAll("#conf-table th[data-sort]").on("click", function () {
      const k = this.dataset.sort;
      state.sortDir = state.sortKey === k ? -state.sortDir : (k === "conf" || k === "areaName" ? 1 : -1);
      state.sortKey = k; renderTable();
    });
    d3.select("#theme-toggle").on("click", () => {
      const root = document.documentElement;
      const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
      root.dataset.theme = dark ? "light" : "dark";
      renderCharts(); renderTable();
    });
    matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { renderCharts(); renderTable(); });
  }

  // ---------- derived data ----------
  function inRange(c) { return c.years.filter((y) => y.year >= state.from && y.year <= state.to); }
  function visibleConfs() {
    const q = state.search;
    return [...byConf.values()].filter((c) => state.supers.has(c.super) &&
      (!q || c.conf.toLowerCase().includes(q) || c.areaName.toLowerCase().includes(q) || c.area.toLowerCase().includes(q)))
      .map((c) => {
        const ys = inRange(c);
        if (!ys.length) return null;
        const last = ys[ys.length - 1];
        const last5 = ys.filter((y) => y.year > last.year - 5);
        return { ...c, ys, lastYear: last.year, accepted: last.accepted, submitted: last.submitted, rate: last.rate,
          mean5: d3.mean(last5, (y) => y.rate) };
      }).filter(Boolean);
  }

  function render() {
    writeHash(); updateHint(); renderChips(); renderCharts(); renderTable(); renderSources();
  }
  function renderCharts() { renderLineChart("rate"); renderLineChart("subs"); renderScatter(); }

  // ---------- chips ----------
  function renderChips() {
    const chips = d3.select("#chips");
    chips.selectAll("*").remove();
    for (const conf of state.selected) {
      const ch = chips.append("span").attr("class", "chip");
      ch.append("span").attr("class", "swatch").style("background", seriesColor(conf));
      ch.append("span").text(conf);
      ch.append("button").attr("aria-label", `Remove ${conf}`).text("×").on("click", () => removeSelected(conf));
    }
    if (state.selected.length > 1)
      chips.append("button").attr("class", "chip clear").text("Clear all").on("click", () => { state.selected = []; state.slotOf.clear(); render(); });
  }

  // ---------- line charts (rate / submissions) ----------
  function renderLineChart(kind) {
    const el = document.getElementById(kind === "rate" ? "rate-chart" : "subs-chart");
    const root = d3.select(el); root.selectAll("*").remove();
    const series = state.selected.map((conf) => ({ conf, values: inRange(byConf.get(conf)) })).filter((s) => s.values.length);
    if (!series.length) { root.append("div").attr("class", "empty").text("No conferences selected."); return; }

    const width = el.clientWidth || 900, height = kind === "rate" ? 300 : 220;
    const m = { top: 10, right: 84, bottom: 26, left: 52 };
    const val = kind === "rate" ? (d) => d.rate : (d) => d.submitted;
    const years = d3.extent(series.flatMap((s) => s.values), (d) => d.year);
    if (years[0] === years[1]) { years[0] -= 1; years[1] += 1; }
    const x = d3.scaleLinear().domain(years).range([m.left, width - m.right]);
    const allV = series.flatMap((s) => s.values.map(val));
    let y;
    if (kind === "rate") y = d3.scaleLinear().domain([0, Math.min(1, d3.max(allV) * 1.08)]).nice().range([height - m.bottom, m.top]);
    else if (state.logSubs) y = d3.scaleLog().domain([Math.max(1, d3.min(allV) * 0.8), d3.max(allV) * 1.2]).range([height - m.bottom, m.top]);
    else y = d3.scaleLinear().domain([0, d3.max(allV) * 1.05]).nice().range([height - m.bottom, m.top]);

    const svg = root.append("svg").attr("width", width).attr("height", height)
      .attr("role", "img").attr("aria-label", `${kind === "rate" ? "Acceptance rate" : "Submissions"} over time for ${series.map((s) => s.conf).join(", ")}`);
    const yTicks = kind === "rate" ? y.ticks(5) : (state.logSubs ? logTicks(y) : y.ticks(5));
    const yFmt = kind === "rate" ? d3.format(".0%") : d3.format("~s");
    svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`)
      .call(d3.axisLeft(y).tickValues(yTicks).tickSize(-(width - m.left - m.right)).tickFormat(""));
    svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
      .call(d3.axisLeft(y).tickValues(yTicks).tickFormat(yFmt).tickSizeOuter(0)).call((g) => g.select(".domain").remove());
    svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`)
      .call(d3.axisBottom(x).ticks(Math.min(12, years[1] - years[0])).tickFormat(d3.format("d")).tickSizeOuter(0));

    const line = d3.line().defined((d) => isFinite(val(d)) && val(d) > 0).x((d) => x(d.year)).y((d) => y(val(d)));
    for (const s of series) {
      const color = seriesColor(s.conf);
      svg.append("path").attr("class", "series-line").attr("stroke", color).attr("d", line(s.values));
      // markers only where a point is isolated (gaps in the series), so single years remain visible
      svg.append("g").selectAll("circle").data(s.values.filter((d, i, a) => !(a[i - 1] && a[i - 1].year === d.year - 1) && !(a[i + 1] && a[i + 1].year === d.year + 1)))
        .join("circle").attr("class", "series-dot").attr("r", 4).attr("fill", color).attr("cx", (d) => x(d.year)).attr("cy", (d) => y(val(d)));
    }
    // direct end labels (<= 4 series get them; legend chips always present), collision-nudged
    if (series.length <= 8) {
      // labels live in the right gutter; a thin leader connects early-ending series
      const gx = width - m.right + 10;
      const labels = series.map((s) => { const l = s.values[s.values.length - 1]; return { conf: s.conf, px: x(l.year), py: y(val(l)), y: y(val(l)) }; })
        .sort((a, b) => a.y - b.y);
      for (let i = 1; i < labels.length; i++) if (labels[i].y - labels[i - 1].y < 14) labels[i].y = labels[i - 1].y + 14;
      const overflow = labels.length ? labels[labels.length - 1].y - (height - m.bottom) : 0;
      if (overflow > 0) for (const l of labels) l.y -= overflow;
      const lg = svg.append("g");
      lg.selectAll("line").data(labels).join("line").attr("stroke", (d) => seriesColor(d.conf)).attr("stroke-width", 1)
        .attr("stroke-dasharray", "2 3").attr("x1", (d) => d.px + 4).attr("y1", (d) => d.py).attr("x2", gx - 3).attr("y2", (d) => d.y);
      lg.selectAll("text").data(labels).join("text").attr("class", "end-label")
        .attr("x", gx).attr("y", (d) => d.y).attr("dy", "0.35em").text((d) => d.conf);
    }

    // crosshair + tooltip
    const cross = svg.append("line").attr("class", "crosshair").attr("y1", m.top).attr("y2", height - m.bottom).style("display", "none");
    const hoverDots = svg.append("g");
    svg.append("rect").attr("class", "hit").attr("x", m.left).attr("y", m.top).attr("width", width - m.left - m.right).attr("height", height - m.top - m.bottom)
      .on("pointermove", (ev) => {
        const [px] = d3.pointer(ev);
        const yr = Math.round(x.invert(px));
        cross.style("display", null).attr("x1", x(yr)).attr("x2", x(yr));
        const pts = series.map((s) => ({ conf: s.conf, d: s.values.find((v) => v.year === yr) })).filter((p) => p.d);
        hoverDots.selectAll("circle").data(pts).join("circle").attr("r", 4.5).attr("class", "series-dot")
          .attr("fill", (p) => seriesColor(p.conf)).attr("cx", x(yr)).attr("cy", (p) => y(val(p.d)));
        if (!pts.length) { hideTip(); return; }
        pts.sort((a, b) => val(b.d) - val(a.d));
        showTip(ev, `<div class="tt-title">${yr}</div>` + pts.map((p) =>
          `<div class="tt-row"><span class="tt-key"><span class="tt-sw" style="background:${seriesColor(p.conf)}"></span>${p.conf}</span>` +
          `<span class="tt-val">${kind === "rate" ? fmtPct(p.d.rate) : fmtInt(p.d.submitted)}</span></div>` +
          `<div class="tt-row muted"><span></span><span>${fmtInt(p.d.accepted)} / ${fmtInt(p.d.submitted)}</span></div>`).join(""));
      })
      .on("pointerleave", () => { cross.style("display", "none"); hoverDots.selectAll("*").remove(); hideTip(); });
  }
  function logTicks(y) {
    const [a, b] = y.domain();
    const out = [];
    for (let p = Math.floor(Math.log10(a)); p <= Math.ceil(Math.log10(b)); p++)
      for (const k of [1, 2, 5]) { const v = k * 10 ** p; if (v >= a && v <= b) out.push(v); }
    return out;
  }

  // ---------- scatter: latest rate vs submissions ----------
  function renderScatter() {
    const el = document.getElementById("scatter");
    const root = d3.select(el); root.selectAll("*").remove();
    const data = visibleConfs();
    d3.select("#scatter-caption").text(`Most recent year in ${state.from}–${state.to} for each conference · ${data.length} shown`);
    if (!data.length) { root.append("div").attr("class", "empty").text("No conferences match the filters."); return; }
    const width = el.clientWidth || 900, height = 390, m = { top: 26, right: 20, bottom: 40, left: 52 };
    const x = d3.scaleLog().domain([d3.min(data, (d) => d.submitted) * 0.8, d3.max(data, (d) => d.submitted) * 1.25]).range([m.left, width - m.right]);
    const y = d3.scaleLinear().domain([0, Math.min(1, d3.max(data, (d) => d.rate) * 1.1)]).nice().range([height - m.bottom, m.top]);
    const svg = root.append("svg").attr("width", width).attr("height", height).attr("role", "img")
      .attr("aria-label", "Scatter plot of acceptance rate versus number of submissions; see table below for values");
    const xt = logTicks(x);
    svg.append("g").attr("class", "grid").attr("transform", `translate(${m.left},0)`).call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.left - m.right)).tickFormat(""));
    svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`).call(d3.axisLeft(y).ticks(5).tickFormat(d3.format(".0%"))).call((g) => g.select(".domain").remove());
    svg.append("g").attr("class", "axis").attr("transform", `translate(0,${height - m.bottom})`).call(d3.axisBottom(x).tickValues(xt).tickFormat(d3.format("~s")).tickSizeOuter(0));
    svg.append("text").attr("x", width - m.right).attr("y", height - 6).attr("text-anchor", "end").attr("font-size", 11).text("Submissions (log scale) →");
    svg.append("text").attr("x", m.left - 44).attr("y", 10).attr("font-size", 11).text("↑ Acceptance rate");

    const sym = d3.symbol().size(90);
    const g = svg.append("g");
    const sorted = data.slice().sort((a, b) => state.selected.includes(a.conf) - state.selected.includes(b.conf));
    g.selectAll("path").data(sorted, (d) => d.conf).join("path")
      .attr("class", (d) => "scatter-mark" + (state.selected.includes(d.conf) ? " selected" : ""))
      .attr("d", (d) => sym.type(SUPER_SHAPE[d.super])())
      .attr("transform", (d) => `translate(${x(d.submitted)},${y(d.rate)})`)
      .attr("fill", (d) => areaColor(d.super))
      .on("pointerenter pointermove", (ev, d) => showTip(ev,
        `<div class="tt-title">${d.conf} ${d.lastYear}</div><div class="muted">${d.areaName}</div>` +
        `<div class="tt-row"><span class="tt-key">Acceptance rate</span><span class="tt-val">${fmtPct(d.rate)}</span></div>` +
        `<div class="tt-row"><span class="tt-key">Accepted / submitted</span><span class="tt-val">${fmtInt(d.accepted)} / ${fmtInt(d.submitted)}</span></div>` +
        `<div class="tt-row"><span class="tt-key">5-yr mean rate</span><span class="tt-val">${fmtPct(d.mean5)}</span></div>` +
        `<div class="muted" style="margin-top:4px">${state.selected.includes(d.conf) ? "Click to remove from comparison" : "Click to compare"}</div>`))
      .on("pointerleave", hideTip)
      .on("click", (_ev, d) => toggleSelected(d.conf));
    // selective labels: selected conferences + the extremes
    const extremes = new Set([d3.least(data, (d) => d.rate), d3.greatest(data, (d) => d.rate), d3.greatest(data, (d) => d.submitted)].filter(Boolean).map((d) => d.conf));
    const labeled = data.filter((d) => state.selected.includes(d.conf) || extremes.has(d.conf));
    // greedy collision avoidance: push a label down if it overlaps an already placed one
    const placed = [];
    const lab = labeled.map((d) => {
      const right = x(d.submitted) > width - 80;
      const w = d.conf.length * 6.5 + 4;
      const lx = right ? x(d.submitted) - 10 - w : x(d.submitted) + 8;
      let ly = y(d.rate);
      for (let tries = 0; tries < 8 && placed.some((p) => Math.abs(p.y - ly) < 12 && lx < p.x + p.w && p.x < lx + w); tries++) ly += 12;
      placed.push({ x: lx, y: ly, w });
      return { d, x: lx, y: ly };
    });
    svg.append("g").selectAll("text").data(lab).join("text").attr("class", "scatter-label")
      .attr("x", (l) => l.x).attr("y", (l) => l.y).attr("dy", "0.35em").text((l) => l.d.conf);
  }

  // ---------- table ----------
  function renderTable() {
    const data = visibleConfs();
    const k = state.sortKey, dir = state.sortDir;
    data.sort((a, b) => (typeof a[k] === "string" ? a[k].localeCompare(b[k]) : a[k] - b[k]) * dir || a.conf.localeCompare(b.conf));
    d3.selectAll("#conf-table th[data-sort]").attr("class", function () {
      const base = this.classList.contains("num") ? "num" : "";
      return base + (this.dataset.sort === k ? (dir > 0 ? " sorted-asc" : " sorted-desc") : "");
    });
    const rows = d3.select("#conf-table tbody").selectAll("tr").data(data, (d) => d.conf).join("tr")
      .attr("class", (d) => (state.selected.includes(d.conf) ? "selected" : null))
      .attr("tabindex", 0).attr("aria-selected", (d) => state.selected.includes(d.conf))
      .on("click", (_ev, d) => toggleSelected(d.conf))
      .on("keydown", (ev, d) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); toggleSelected(d.conf); } });
    rows.html((d) =>
      `<td class="conf-name">${esc(d.conf)}</td>` +
      `<td><span class="area-tag" data-super="${d.super}"><span class="shape" style="background:${areaColor(d.super)}"></span>${esc(d.areaName)}</span></td>` +
      `<td class="num">${d.lastYear}</td><td class="num">${fmtInt(d.accepted)}</td><td class="num">${fmtInt(d.submitted)}</td>` +
      `<td class="num">${fmtPct(d.rate)}</td><td class="num">${fmtPct(d.mean5)}</td><td class="spark-col"></td>`);
    rows.select(".spark-col").each(function (d) { sparkline(this, d); });
  }
  function sparkline(td, d) {
    const w = 120, h = 24, ys = d.ys;
    const svg = d3.select(td).append("svg").attr("width", w).attr("height", h).attr("aria-hidden", "true");
    if (ys.length < 2) return;
    const x = d3.scaleLinear().domain([state.from, state.to]).range([2, w - 4]);
    const y = d3.scaleLinear().domain([0, d3.max(ys, (v) => v.rate)]).range([h - 3, 3]);
    const color = state.selected.includes(d.conf) ? seriesColor(d.conf) : css("--text-muted");
    svg.append("path").attr("fill", "none").attr("stroke", color).attr("stroke-width", 1.5)
      .attr("d", d3.line().x((v) => x(v.year)).y((v) => y(v.rate))(ys));
    const l = ys[ys.length - 1];
    svg.append("circle").attr("r", 2.5).attr("fill", color).attr("cx", x(l.year)).attr("cy", y(l.rate));
  }

  // ---------- sources table ----------
  function renderSources() {
    const panel = document.getElementById("sources-panel");
    panel.hidden = !state.selected.length;
    const rows = state.selected.flatMap((conf) => inRange(byConf.get(conf)).slice().reverse()
      .flatMap((y) => y.rows.map((r) => ({ conf, r }))));
    d3.select("#sources-table tbody").selectAll("tr").data(rows).join("tr").html(({ conf, r }) => {
      const a = +r.Accepted, s = +r.Submitted;
      const src = r.Source || "";
      const srcHtml = /^https?:\/\//.test(src) ? `<a href="${esc(src)}" rel="noopener">${esc(src.replace(/^https?:\/\/(www\.)?/, ""))}</a>` : esc(src);
      return `<td><span class="tt-sw" style="display:inline-block;width:10px;height:3px;border-radius:2px;margin-right:6px;vertical-align:middle;background:${seriesColor(conf)}"></span>${esc(conf)}</td>` +
        `<td class="num">${r.Year}${+r.Sequence > 1 || hasSeq(conf, r.Year) ? ` <span class="muted">(cycle ${r.Sequence})</span>` : ""}</td>` +
        `<td class="num">${fmtInt(a)}</td><td class="num">${fmtInt(s)}</td><td class="num">${s ? fmtPct(a / s) : ""}</td>` +
        `<td class="src-cell" title="${esc(src)}">${srcHtml}</td><td class="notes-cell">${esc(r.Notes || "")}</td>`;
    });
  }
  function hasSeq(conf, year) { const y = byConf.get(conf).years.find((v) => v.year === +year); return y && y.rows.length > 1; }

  // ---------- tooltip & utils ----------
  function showTip(ev, html) {
    tip.innerHTML = html; tip.hidden = false;
    const pad = 14, r = tip.getBoundingClientRect();
    let left = ev.clientX + pad, top = ev.clientY + pad;
    if (left + r.width > innerWidth - 8) left = ev.clientX - r.width - pad;
    if (top + r.height > innerHeight - 8) top = ev.clientY - r.height - pad;
    tip.style.left = left + "px"; tip.style.top = top + "px";
  }
  function hideTip() { tip.hidden = true; }
  function esc(s) { return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
  function debounce(f, ms) { let t; return () => { clearTimeout(t); t = setTimeout(f, ms); }; }
})();
