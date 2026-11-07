/* =========================================================
   Recall Insights: mastery dashboard, spaced-repetition queue,
   calibration chart and prerequisite knowledge graph.
   Charts are lazy-loaded from pinned CDN builds; every section
   has an offline fallback so the page never breaks.
   ========================================================= */
(function () {
  "use strict";
  const LR = window.RecallLearning;
  const UI = () => window.RecallUI;
  const esc = (s) => UI().esc(s);

  const LIBS = {
    chart: { src: "https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.min.js", sri: "sha384-T/4KgSWuZEPozpPz7rnnp/5lDSnpY1VPJCojf1S81uTHS1E38qgLfMgVsAeRCWc4", ok: () => window.Chart },
    vis: { src: "https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js", sri: "sha384-yxKDWWf0wwdUj/gPeuL11czrnKFQROnLgY8ll7En9NYoXibgg3C6NK/UDHNtUgWJ", ok: () => window.vis },
  };
  const loading = {};
  function loadLib(name) {
    const lib = LIBS[name];
    if (lib.ok()) return Promise.resolve(true);
    if (loading[name]) return loading[name];
    loading[name] = new Promise((resolve) => {
      const s = document.createElement("script");
      s.src = lib.src; s.integrity = lib.sri; s.crossOrigin = "anonymous"; s.async = true;
      s.onload = () => resolve(!!lib.ok());
      s.onerror = () => { delete loading[name]; resolve(false); };  // offline: allow a retry later
      document.head.appendChild(s);
    });
    return loading[name];
  }

  const COLORS = { weak: "#f0919f", developing: "#e6c068", strong: "#6fd8a0", mastered: "#6fd8a0", untried: "#5a6a99", ink: "#b4c6ee", line: "rgba(176,200,255,.16)", accent: "#9ebbff" };
  const bandOf = (c) => (c.n === 0 ? "untried" : LR.band(c.pL));
  const pct = (x) => Math.round(x * 100);
  const cls = (p) => (p < 40 ? "bad" : p < 80 ? "warn" : "ok");
  const bar = (p) => `<span class="mastery-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${p}" aria-label="Mastery ${p}%"><span class="${cls(p)}" style="width:${p}%"></span></span>`;

  let chartA = null, chartB = null, network = null, token = 0;
  function destroy() {
    [chartA, chartB].forEach((c) => c && c.destroy());
    chartA = chartB = null;
    if (network) { network.destroy(); network = null; }
  }

  function svgLine(values, w = 520, h = 140) {  // offline fallback for the trend chart
    if (values.length < 2) return "";
    const step = w / (values.length - 1);
    const pts = values.map((v, i) => `${(i * step).toFixed(1)},${(h - (v / 100) * (h - 12) - 6).toFixed(1)}`).join(" ");
    return `<svg viewBox="0 0 ${w} ${h}" class="svg-trend" role="img" aria-label="Accuracy trend"><polyline points="${pts}" fill="none" stroke="${COLORS.accent}" stroke-width="2.5"/></svg>`;
  }
  function treeFallback(st) {  // offline fallback for the graph: prerequisite lists
    const names = (k) => (st.concepts[k] || st.graph.nodes[k] || { name: k }).name;
    const kids = {};
    st.graph.edges.forEach(([a, b]) => { (kids[b] = kids[b] || []).push(a); });
    const keys = Object.keys(kids);
    if (!keys.length) return `<p class="muted">No prerequisite links yet. They appear after quizzes that list concepts.</p>`;
    return `<ul class="tree">${keys.map((k) => `<li><b>${esc(names(k))}</b> needs: ${kids[k].map((p) => esc(names(p))).join(", ")}</li>`).join("")}</ul>`;
  }

  function render(container) {
    destroy();
    const my = ++token;
    const st = LR.state();
    const concepts = LR.conceptList();
    const tried = concepts.filter((c) => c.n > 0);
    const due = LR.dueCards();
    const cal = LR.calibration(st.attempts);
    const rec = LR.recommend();
    const mastered = tried.filter((c) => c.pL >= 0.95).length;
    const needs = tried.filter((c) => c.pL < 0.5);
    const strong = tried.filter((c) => c.pL >= 0.8).reverse();

    if (!tried.length && !st.sessions.length) {
      container.innerHTML = `<div class="rev-head"><h2>Insights</h2></div>
        <div class="empty-state">${UI().ico("chart")}<p>No learning data yet. Finish a quiz and Recall will track mastery, schedule reviews and map your concepts.</p></div>`;
      return;
    }

    const dueByConcept = {};
    due.forEach((c) => { dueByConcept[c.concept] = (dueByConcept[c.concept] || 0) + 1; });
    const top = rec.details[0];
    const mis = LR.weakMisconceptions(6);

    container.innerHTML = `
      <div class="rev-head"><h2>Insights</h2>
        <div class="row-actions" style="margin:0"><button class="btn ghost sm" data-ins="export">${UI().ico("download")}Export</button>
        <button class="btn ghost sm" data-ins="import">${UI().ico("upload")}Import</button>
        <button class="btn ghost sm" data-ins="reset">${UI().ico("trash")}Reset</button>
        <input type="file" id="insImport" accept="application/json" hidden></div></div>

      <div class="metrics">
        <div class="metric glass"><div class="v">${tried.length}</div><div class="l">Concepts tracked</div></div>
        <div class="metric glass"><div class="v">${mastered}</div><div class="l">Mastered (95%+)</div></div>
        <div class="metric glass"><div class="v">${due.length}</div><div class="l">Cards due now</div></div>
        <div class="metric glass"><div class="v">${cal.brier == null ? "—" : Math.round((1 - cal.brier) * 100) + "%"}</div><div class="l">Calibration</div></div>
      </div>

      ${top ? `<section class="panel-block glass root-cause" aria-label="Recommended next"><div class="panel-title">${UI().ico("target")} Recommended next</div>
        <p><b>${esc(top.name)}</b> <span class="muted">· ${esc(top.reason)} · mastery ${pct(top.pL)}%</span></p>
        <div class="row-actions"><button class="btn primary sm" data-ins="practice" data-c="${esc(top.name)}">${UI().ico("spark")}Practice this concept</button>
        <button class="btn sm" data-ins="adaptive">${UI().ico("brain")}Adaptive quiz</button></div></section>` : ""}

      <section class="panel-block glass" aria-label="Spaced repetition"><div class="panel-title">${UI().ico("clock")} Spaced repetition</div>
        ${due.length ? `<p>${due.length} question${due.length > 1 ? "s" : ""} due: ${Object.entries(dueByConcept).slice(0, 6).map(([c, n]) => `${esc(c)} (${n})`).join(", ")}</p>
          <div class="row-actions"><button class="btn primary sm" data-ins="revise">${UI().ico("play")}Start revision (${Math.min(15, due.length)})</button></div>`
          : `<p class="muted">Nothing due. ${Object.keys(st.cards).length} card${Object.keys(st.cards).length === 1 ? "" : "s"} scheduled.</p>`}</section>

      <div class="ins-grid">
        <section class="panel-block glass" aria-label="Needs work"><div class="panel-title">${UI().ico("x")} Needs work</div>
          ${needs.length ? needs.slice(0, 8).map((c) => `<div class="m-row"><span>${esc(c.name)}</span>${bar(pct(c.pL))}<small>${pct(c.pL)}%</small></div>`).join("") : `<p class="muted">No weak concepts. Nice.</p>`}</section>
        <section class="panel-block glass" aria-label="Strengths"><div class="panel-title">${UI().ico("check")} Strengths</div>
          ${strong.length ? strong.slice(0, 8).map((c) => `<div class="m-row"><span>${esc(c.name)}</span>${bar(pct(c.pL))}<small>${pct(c.pL)}%</small></div>`).join("") : `<p class="muted">Keep practising to build strengths.</p>`}</section>
      </div>

      <div class="ins-grid">
        <section class="panel-block glass" aria-label="Accuracy trend"><div class="panel-title">${UI().ico("chart")} Accuracy trend</div>
          <div class="chart-wrap" id="trendBox"></div></section>
        <section class="panel-block glass" aria-label="Confidence calibration"><div class="panel-title">${UI().ico("target")} Confidence vs accuracy</div>
          <div class="chart-wrap" id="calBox"></div></section>
      </div>

      <section class="panel-block glass" aria-label="Knowledge graph"><div class="panel-title">${UI().ico("graph")} Knowledge graph
        <span class="legend"><i style="background:${COLORS.weak}"></i>weak <i style="background:${COLORS.developing}"></i>developing <i style="background:${COLORS.strong}"></i>strong <i style="background:${COLORS.untried}"></i>not tried</span></div>
        <div class="graph-box" id="graphBox"></div>
        <div class="graph-side" id="graphSide" aria-live="polite"><span class="muted">Click a concept to see details.</span></div></section>

      <section class="panel-block glass" aria-label="Recurring misconceptions"><div class="panel-title">${UI().ico("brain")} Recurring misconceptions</div>
        ${mis.length ? `<ul class="kp">${mis.map((m) => `<li class="miss">${UI().ico("x")}<span><b>${esc(m.concept)}</b>: ${esc(m.misc)} <small class="muted">×${m.count}</small></span></li>`).join("")}</ul>`
          : `<p class="muted">No repeated mistakes logged yet.</p>`}</section>`;

    wire(container);

    // ---- charts (lazy)
    const sess = st.sessions.filter((x) => x.total);
    const series = sess.map((x) => Math.round((100 * x.correct) / x.total));
    const ma = series.map((_, i) => { const w = series.slice(Math.max(0, i - 4), i + 1); return Math.round(w.reduce((a, b) => a + b, 0) / w.length); });
    const trendBox = container.querySelector("#trendBox"), calBox = container.querySelector("#calBox");
    trendBox.innerHTML = series.length >= 2 ? svgLine(series) : `<p class="muted">Finish two quizzes to see a trend.</p>`;
    calBox.innerHTML = cal.n ? "" : `<p class="muted">Answer with Guess / Unsure / Sure to see calibration.</p>`;

    loadLib("chart").then((ok) => {
      if (my !== token || !ok) return;
      Chart.defaults.color = COLORS.ink; Chart.defaults.borderColor = COLORS.line;
      if (series.length >= 2) {
        trendBox.innerHTML = '<canvas aria-label="Accuracy trend chart" role="img"></canvas>';
        chartA = new Chart(trendBox.firstChild, { type: "line", data: { labels: series.map((_, i) => i + 1), datasets: [
          { label: "Score %", data: series, borderColor: COLORS.accent, backgroundColor: "rgba(158,187,255,.15)", tension: 0.3, fill: true },
          { label: "5-quiz average", data: ma, borderColor: COLORS.strong, borderDash: [5, 4], pointRadius: 0, tension: 0.3 }] },
          options: { maintainAspectRatio: false, scales: { y: { min: 0, max: 100 } }, animation: { duration: 250 } } });
      }
      if (cal.n) {
        calBox.innerHTML = '<canvas aria-label="Confidence calibration chart" role="img"></canvas>';
        const lv = ["guess", "unsure", "sure"];
        chartB = new Chart(calBox.firstChild, { type: "bar", data: { labels: ["Guess", "Unsure", "Sure"], datasets: [
          { label: "Actual accuracy %", data: lv.map((k) => (cal.levels[k].n ? Math.round((100 * cal.levels[k].r) / cal.levels[k].n) : 0)), backgroundColor: COLORS.accent },
          { type: "line", label: "Expected %", data: [25, 60, 90], borderColor: COLORS.developing, borderDash: [5, 4], pointRadius: 3 }] },
          options: { maintainAspectRatio: false, scales: { y: { min: 0, max: 100 } }, animation: { duration: 250 },
            plugins: { tooltip: { callbacks: { afterLabel: (c) => (c.datasetIndex === 0 ? `${cal.levels[lv[c.dataIndex]].n} answers` : "") } } } } });
      }
    });

    // ---- graph (lazy)
    const box = container.querySelector("#graphBox");
    box.innerHTML = treeFallback(st);
    const keys = new Set([...Object.keys(st.graph.nodes), ...Object.keys(st.concepts)]);
    if (keys.size) {
      loadLib("vis").then((ok) => {
        if (my !== token || !ok) return;
        const ranked = [...keys].map((k) => st.concepts[k] || { name: (st.graph.nodes[k] || {}).name || k, n: 0, pL: 0.3, last: 0 })
          .map((c, i) => ({ k: [...keys][i], c })).sort((a, b) => b.c.n - a.c.n || b.c.last - a.c.last).slice(0, 120);
        const keep = new Set(ranked.map((r) => r.k));
        const nodes = new vis.DataSet(ranked.map(({ k, c }) => ({ id: k, label: c.name, value: Math.max(1, c.n),
          color: { background: COLORS[bandOf(c)], border: COLORS[bandOf(c)], highlight: { background: COLORS[bandOf(c)], border: "#fff" } },
          font: { color: "#e6eeff", size: 14 } })));
        const edges = new vis.DataSet(st.graph.edges.filter(([a, b]) => keep.has(a) && keep.has(b)).map(([a, b]) => ({ from: a, to: b, arrows: "to", color: { color: "rgba(176,200,255,.45)" } })));
        box.innerHTML = "";
        network = new vis.Network(box, { nodes, edges }, {
          nodes: { shape: "dot", scaling: { min: 10, max: 26 } },
          physics: { solver: "barnesHut", stabilization: { iterations: 150 } },
          interaction: { hover: true, tooltipDelay: 150 },
        });
        network.once("stabilizationIterationsDone", () => network && network.setOptions({ physics: false }));
        network.on("click", (p) => {
          const side = container.querySelector("#graphSide");
          if (!p.nodes.length) return;
          const k = p.nodes[0], c = st.concepts[k];
          if (!c) return;
          const pre = st.graph.edges.filter(([, b]) => b === k).map(([a]) => (st.concepts[a] || {}).name || a);
          side.innerHTML = `<b>${esc(c.name)}</b> · mastery ${pct(c.pL)}% (${LR.band(c.pL)}) · ${c.n} attempt${c.n === 1 ? "" : "s"} · ${LR.cardsForConcept(c.name).length} cards
            ${pre.length ? `<br><span class="muted">Needs: ${pre.map(esc).join(", ")}</span>` : ""}
            <div class="row-actions"><button class="btn primary sm" data-ins="practice" data-c="${esc(c.name)}">${UI().ico("spark")}Practice concept</button></div>`;
        });
      });
    }
  }

  function wire(container) {
    container.onclick = async (e) => {
      const b = e.target.closest("[data-ins]");
      if (!b) return;
      const a = b.dataset.ins;
      if (a === "practice") UI().practiceConcept(b.dataset.c);
      else if (a === "adaptive") UI().adaptiveNext();
      else if (a === "revise") UI().startRevision();
      else if (a === "export") UI().download("recall-learning.json", LR.exportJSON(), "application/json");
      else if (a === "import") container.querySelector("#insImport").click();
      else if (a === "reset" && (await UI().ask("Delete all mastery, review schedules and the knowledge graph? This cannot be undone.", "Delete"))) {
        LR.reset(); UI().renderDue(); render(container); UI().toast("Learning data cleared.");
      }
    };
    const f = container.querySelector("#insImport");
    if (f) f.onchange = async () => {
      try { LR.importJSON(await f.files[0].text()); UI().renderDue(); render(container); UI().toast("Learning data imported."); }
      catch { UI().toast("That file is not a valid Recall export.", true); }
    };
  }

  window.RecallInsights = { render };
})();
