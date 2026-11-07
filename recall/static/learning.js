/* =========================================================
   Recall learning core: BKT mastery, SM-2 scheduling, concept graph,
   confidence calibration. Pure logic (no DOM) so it can be unit-tested.
   State lives in localStorage["recall.learning"] (version 1).
   ========================================================= */
(function (root) {
  "use strict";

  const KEY = "recall.learning";
  const DAY = 86400000;
  const CAPS = { attempts: 600, sessions: 120, cards: 300, concepts: 200, edges: 600 };
  const P_INIT = 0.3;
  const BKT = {
    mcq: { G: 0.25, S: 0.10, T: 0.15 },
    short: { G: 0.10, S: 0.12, T: 0.18 },
    coding: { G: 0.05, S: 0.15, T: 0.20 },
  };
  const CONF_P = { guess: 0.25, unsure: 0.6, sure: 0.9 };

  const empty = () => ({ version: 1, concepts: {}, cards: {}, attempts: [], sessions: [], graph: { nodes: {}, edges: [] } });
  let state = null;
  let dirty = false;
  let saveTimer = null;
  let saveIsIdle = false;
  let onError = null;

  /* ---------------- helpers ---------------- */
  const norm = (s) => String(s || "").trim().replace(/\s+/g, " ");
  const keyOf = (name) => norm(name).toLowerCase();
  const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
  function fnv1a(str) {
    let h = 0x811c9dc5;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    return h >>> 0;
  }
  const qid = (q) => "q_" + fnv1a((q.type || "mcq") + ":" + norm(q.question).toLowerCase()).toString(16);
  const band = (p) => (p < 0.4 ? "weak" : p < 0.8 ? "developing" : p < 0.95 ? "strong" : "mastered");

  /* ---------------- storage ---------------- */
  function migrate(s) {
    if (!s || typeof s !== "object" || !s.concepts || !s.cards) throw new Error("bad state");
    s.attempts = Array.isArray(s.attempts) ? s.attempts : [];
    s.sessions = Array.isArray(s.sessions) ? s.sessions : [];
    s.graph = s.graph && s.graph.nodes ? s.graph : { nodes: {}, edges: [] };
    s.graph.edges = Array.isArray(s.graph.edges) ? s.graph.edges : [];
    s.version = 1;
    return s;
  }
  function load() {
    let raw = null;
    try { raw = localStorage.getItem(KEY); } catch { /* storage blocked */ }
    if (!raw) { state = empty(); return state; }
    try { state = migrate(JSON.parse(raw)); }
    catch {
      try { localStorage.setItem(KEY + ".bak", raw); } catch { /* ignore */ }
      state = empty();
    }
    return state;
  }
  const S = () => state || load();

  function enforceCaps(s, factor = 1) {
    const cap = (n) => Math.max(10, Math.floor(n * factor));
    if (s.attempts.length > cap(CAPS.attempts)) s.attempts = s.attempts.slice(-cap(CAPS.attempts));
    if (s.sessions.length > cap(CAPS.sessions)) s.sessions = s.sessions.slice(-cap(CAPS.sessions));
    if (s.graph.edges.length > cap(CAPS.edges)) s.graph.edges = s.graph.edges.slice(-cap(CAPS.edges));
    const cards = Object.values(s.cards);
    if (cards.length > cap(CAPS.cards)) {
      const now = Date.now();
      // evict not-due cards with the longest interval (best known) first, oldest first
      const evictable = cards.filter((c) => c.due > now).sort((a, b) => b.interval - a.interval || a.last - b.last);
      let extra = cards.length - cap(CAPS.cards);
      for (const c of evictable) { if (extra-- <= 0) break; delete s.cards[c.qid]; }
    }
    const cons = Object.entries(s.concepts);
    if (cons.length > cap(CAPS.concepts)) {
      cons.sort((a, b) => a[1].n - b[1].n || a[1].last - b[1].last);
      let extra = cons.length - cap(CAPS.concepts);
      for (const [k] of cons) { if (extra-- <= 0) break; delete s.concepts[k]; delete s.graph.nodes[k]; }
      s.graph.edges = s.graph.edges.filter(([a, b]) => s.concepts[a] && s.concepts[b]);
    }
  }
  function writeNow() {
    if (saveTimer != null) { if (saveIsIdle && typeof cancelIdleCallback === "function") cancelIdleCallback(saveTimer); else clearTimeout(saveTimer); }
    saveTimer = null;
    if (!dirty || !state) return true;
    enforceCaps(state);
    for (let attempt = 0; attempt < 2; attempt++) {
      try { localStorage.setItem(KEY, JSON.stringify(state)); dirty = false; return true; }
      catch (e) {
        enforceCaps(state, 0.75);  // quota: prune 25% and retry once
        if (attempt) { if (onError) onError(e); return false; }
      }
    }
    return false;
  }
  function save(immediate) {
    dirty = true;
    if (immediate) return writeNow();
    if (saveTimer != null) return true;
    const run = () => { saveTimer = null; writeNow(); };
    saveIsIdle = typeof requestIdleCallback === "function";
    saveTimer = saveIsIdle ? requestIdleCallback(run, { timeout: 400 }) : setTimeout(run, 50);
    return true;
  }
  function reset() { state = empty(); dirty = true; writeNow(); return state; }
  function importJSON(text) { const s = migrate(JSON.parse(text)); state = s; dirty = true; writeNow(); return state; }
  const exportJSON = () => JSON.stringify(S(), null, 2);

  /* ---------------- quiz normalisation (mirrors server _validate defaults) ---------------- */
  function normalizeQuiz(quiz) {
    const out = { ...quiz, concepts: Array.isArray(quiz.concepts) ? quiz.concepts.slice() : [] };
    const known = new Set(out.concepts.map((c) => keyOf(c.name)));
    const fix = (q, type) => {
      const c = { ...q };
      c.concept = norm(c.concept) || "General";
      if (!known.has(keyOf(c.concept))) { known.add(keyOf(c.concept)); out.concepts.push({ name: c.concept, prereqs: [] }); }
      if (type === "mcq") {
        const m = Array.isArray(c.misconceptions) && c.misconceptions.length === 4 ? c.misconceptions.slice() : [null, null, null, null];
        m[c.answer_index] = null;
        c.misconceptions = m;
      }
      return c;
    };
    ["mcq", "short", "coding"].forEach((t) => { out[t] = (quiz[t] || []).map((q) => fix(q, t)); });
    return out;
  }

  /* ---------------- BKT ---------------- */
  function bktUpdate(p, correct, conf, type, kind) {
    const base = BKT[type] || BKT.mcq;
    let G = base.G, Sl = base.S, w = 1;
    if (conf === "sure") { G *= 0.5; Sl *= 0.5; }
    else if (conf === "guess") { G = Math.min(0.5, G * 1.4); w = 0.45; }
    if (kind === "retry" && correct) w *= 0.3;
    const post = correct
      ? (p * (1 - Sl)) / (p * (1 - Sl) + (1 - p) * G)
      : (p * Sl) / (p * Sl + (1 - p) * (1 - G));
    const obs = (1 - w) * p + w * post;
    const Teff = correct ? w * base.T : 0.02;
    return clamp(obs + (1 - obs) * Teff, 0.02, 0.99);
  }

  /* ---------------- SM-2 ---------------- */
  function quality(correct, conf) {
    if (correct) return conf === "sure" ? 5 : conf === "guess" ? 3 : 4;
    return conf === "sure" ? 0 : conf === "guess" ? 2 : 1;
  }
  function sm2Update(card, correct, conf, now) {
    const q = quality(correct, conf);
    if (q < 3) {
      card.reps = 0; card.interval = 1; card.lapses++;
      card.due = q === 0 ? now : now + DAY;  // confident misconception: due immediately
    } else {
      card.interval = card.reps === 0 ? 1 : card.reps === 1 ? 6 : Math.round(card.interval * card.ef);
      card.reps++;
      card.due = now + card.interval * DAY;
    }
    card.ef = Math.max(1.3, card.ef + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02));
    card.last = now;
    return card;
  }

  /* ---------------- concepts & graph ---------------- */
  function ensureConcept(name, now) {
    const s = S(), k = keyOf(name);
    if (!k) return null;
    if (!s.concepts[k]) s.concepts[k] = { name: norm(name), pL: P_INIT, n: 0, correct: 0, last: now || Date.now(), topics: [] };
    if (!s.graph.nodes[k]) s.graph.nodes[k] = { name: norm(name) };
    return s.concepts[k];
  }
  function reaches(edges, from, to) {  // is there a path from -> to ? (iterative, visited set)
    const adj = {};
    edges.forEach(([a, b]) => { (adj[a] = adj[a] || []).push(b); });
    const seen = new Set([from]), stack = [from];
    while (stack.length) {
      const u = stack.pop();
      if (u === to) return true;
      for (const v of adj[u] || []) if (!seen.has(v)) { seen.add(v); stack.push(v); }
    }
    return false;
  }
  function mergeGraph(concepts, title) {
    const s = S(), now = Date.now();
    (concepts || []).forEach((c) => {
      const cc = ensureConcept(c.name, now);
      if (!cc) return;
      if (title && !cc.topics.includes(title)) { cc.topics.unshift(title); cc.topics = cc.topics.slice(0, 5); }
      const tk = keyOf(c.name);
      (c.prereqs || []).forEach((p) => {
        const pk = keyOf(p);
        if (!pk || pk === tk) return;
        ensureConcept(p, now);
        if (s.graph.edges.some(([a, b]) => a === pk && b === tk)) return;
        if (reaches(s.graph.edges, tk, pk)) return;  // would create a cycle: reject
        s.graph.edges.push([pk, tk]);
      });
    });
    save();
  }

  /* ---------------- recording ---------------- */
  function snapshot(item) { return JSON.parse(JSON.stringify(item)); }
  function recordAttempt(a) {
    // a: {item, correct:true|false|null, conf, kind, pick, misc, difficulty, mode}
    const s = S(), now = Date.now();
    const item = a.item, id = item.qid || qid(item);
    const concept = norm(item.concept) || "General";
    if (a.correct == null) return null;
    const c = ensureConcept(concept, now);
    c.pL = bktUpdate(c.pL, a.correct, a.conf || null, item.type, a.kind);
    c.n++; if (a.correct) c.correct++;
    c.last = now;
    if (a.kind !== "retry") {
      let card = s.cards[id];
      if (!card) card = s.cards[id] = { qid: id, concept, ef: 2.5, interval: 0, reps: 0, lapses: 0, due: now, last: now, item: snapshot(item) };
      else card.item = snapshot(item);
      card.concept = concept;
      sm2Update(card, a.correct, a.conf || null, now);
    }
    const rec = { ts: now, qid: id, concept, type: item.type, correct: a.correct, conf: a.conf || null, kind: a.kind || "quiz", misc: a.misc || null };
    s.attempts.push(rec);
    save();
    return rec;
  }
  function recordSession(sess) {
    const s = S();
    const att = sess.attempts || [];
    const cal = calibration(att);
    s.sessions.push({ id: sess.id, ts: Date.now(), title: sess.title, kind: sess.kind || "quiz", total: sess.total, correct: sess.correct,
      brier: cal.brier, quads: cal.quads });
    save();
  }

  /* ---------------- queries ---------------- */
  const dueCards = (now = Date.now()) => Object.values(S().cards)
    .filter((c) => c.due <= now)
    .sort((a, b) => a.due - b.due || ((S().concepts[keyOf(a.concept)] || {}).pL || 0) - ((S().concepts[keyOf(b.concept)] || {}).pL || 0));
  const cardsForConcept = (name) => Object.values(S().cards).filter((c) => keyOf(c.concept) === keyOf(name));
  const conceptList = () => Object.values(S().concepts).sort((a, b) => a.pL - b.pL);
  const vocab = (limit = 40) => Object.values(S().concepts).sort((a, b) => b.last - a.last).slice(0, limit).map((c) => c.name);

  function upstream(k) {  // all ancestors via BFS with explicit visited set -> [{key, depth}]
    const edges = S().graph.edges, parents = {};
    edges.forEach(([a, b]) => { (parents[b] = parents[b] || []).push(a); });
    const seen = new Set([k]), out = [];
    let layer = [k], depth = 0;
    while (layer.length && depth < 8) {
      depth++;
      const next = [];
      for (const u of layer) for (const p of parents[u] || []) if (!seen.has(p)) { seen.add(p); out.push({ key: p, depth }); next.push(p); }
      layer = next;
    }
    return out;
  }
  function weakMisconceptions(limit = 8) {
    const map = {};
    S().attempts.forEach((a) => {
      if (a.correct === false && a.misc) {
        const k = keyOf(a.concept) + "|" + a.misc;
        (map[k] = map[k] || { concept: a.concept, misc: a.misc, count: 0, last: 0 });
        map[k].count++; map[k].last = a.ts;
      }
    });
    return Object.values(map).sort((a, b) => b.count - a.count || b.last - a.last).slice(0, limit);
  }
  function suggestDifficulty(names) {
    const cons = S().concepts;
    let list = (names || []).map((n) => cons[keyOf(n)]).filter((c) => c && c.n > 0);
    if (!list.length) list = Object.values(cons).filter((c) => c.n > 0);
    const levels = ["Easy", "Medium", "Hard"];
    if (!list.length) return "Medium";
    const mean = list.reduce((a, c) => a + c.pL, 0) / list.length;
    let idx = mean < 0.4 ? 0 : mean > 0.75 ? 2 : 1;
    const last = S().sessions.filter((x) => x.total).slice(-1)[0];
    if (last) {
      const pct = (100 * last.correct) / last.total;
      if (pct >= 85) idx = Math.min(2, idx + 1); else if (pct <= 40) idx = Math.max(0, idx - 1);
    }
    return levels[idx];
  }
  function recommend(count = 4) {
    const s = S(), cons = s.concepts;
    let weak = Object.entries(cons).filter(([, c]) => c.n > 0 && c.pL < 0.45).sort((a, b) => a[1].pL - b[1].pL);
    if (!weak.length) weak = Object.entries(cons).filter(([, c]) => c.n > 0).sort((a, b) => a[1].pL - b[1].pL).slice(0, 2);
    const picked = new Map();
    for (const [k, c] of weak) {
      let target = { key: k, reason: "Weak concept", pL: c.pL };
      const ups = upstream(k).filter((u) => cons[u.key] && (cons[u.key].n === 0 || cons[u.key].pL < 0.6));
      if (ups.length) {  // root-cause: deepest weak / untried prerequisite first
        ups.sort((a, b) => b.depth - a.depth || cons[a.key].pL - cons[b.key].pL);
        const u = ups[0];
        target = { key: u.key, reason: "Prerequisite of " + c.name, pL: cons[u.key].pL };
      }
      if (!picked.has(target.key)) picked.set(target.key, target);
      if (picked.size >= count) break;
    }
    const details = [...picked.values()].map((t) => ({ name: cons[t.key].name, reason: t.reason, pL: t.pL }));
    const names = details.map((d) => d.name);
    const notes = weakMisconceptions(3).filter((m) => names.some((n) => keyOf(n) === keyOf(m.concept)) || !names.length).map((m) => m.misc);
    return { concepts: names, notes, difficulty: suggestDifficulty(names), details };
  }
  function calibration(attempts) {
    const rows = (attempts || []).filter((a) => a.conf && a.correct != null);
    const lv = { guess: { n: 0, r: 0 }, unsure: { n: 0, r: 0 }, sure: { n: 0, r: 0 } };
    const quads = { solid: 0, fragile: 0, gap: 0, blind: 0 };
    let brier = 0;
    rows.forEach((a) => {
      const y = a.correct ? 1 : 0;
      lv[a.conf].n++; lv[a.conf].r += y;
      brier += (CONF_P[a.conf] - y) ** 2;
      if (a.conf === "sure") quads[y ? "solid" : "blind"]++; else quads[y ? "fragile" : "gap"]++;
    });
    return { n: rows.length, brier: rows.length ? brier / rows.length : null, quads, levels: lv };
  }

  const L = {
    KEY, CAPS, P_INIT, empty, load, save, reset, importJSON, exportJSON, state: S,
    qid, band, keyOf, normalizeQuiz, bktUpdate, quality, sm2Update, ensureConcept, mergeGraph, reaches,
    recordAttempt, recordSession, dueCards, cardsForConcept, conceptList, vocab, upstream,
    weakMisconceptions, suggestDifficulty, recommend, calibration, flush: () => { dirty = true; return writeNow(); },
    onError: (fn) => { onError = fn; },
    _setState: (s) => { state = s; },
  };
  root.RecallLearning = L;
  if (typeof module !== "undefined" && module.exports) module.exports = L;
  if (typeof window !== "undefined") window.addEventListener("pagehide", () => { if (dirty) writeNow(); });
})(typeof self !== "undefined" ? self : this);
