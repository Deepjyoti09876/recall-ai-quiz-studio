/* =========================================================
   Recall · AI Quiz Studio — frontend logic (no build step)
   ========================================================= */
(() => {
  "use strict";

  /* ---------------- icons (inline SVG, lucide-style) ---------------- */
  const P = {
    home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V20a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V9.5"/>',
    globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18a14 14 0 0 1 0-18"/>',
    file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1A1.7 1.7 0 0 0 9 19.4a1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 4.6 9a1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    arrowRight: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    arrowLeft: '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
    clip: '<path d="m21 11-8.6 8.6a5 5 0 0 1-7-7l8.5-8.6a3.3 3.3 0 0 1 4.7 4.7l-8.6 8.6a1.7 1.7 0 0 1-2.4-2.4l7.9-7.9"/>',
    wave: '<path d="M4 10v4M8 7v10M12 4v16M16 7v10M20 10v4"/>',
    sliders: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    upload: '<path d="M12 16V4M6 10l6-6 6 6"/><path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/>',
    list: '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/>',
    pen: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    code: '<path d="m8 8-5 4 5 4M16 8l5 4-5 4M14 4l-4 16"/>',
    timer: '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M9 2h6"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    x: '<path d="M18 6 6 18M6 6l12 12"/>',
    minus: '<path d="M5 12h14"/>',
    flag: '<path d="M4 22V4M4 4h13l-2 4 2 4H4"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h0"/>',
    play: '<path d="m7 4 13 8-13 8z"/>',
    replay: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>',
    download: '<path d="M12 4v12M6 10l6 6 6-6M4 20h16"/>',
    trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    spark: '<path d="M12 2.5l2.4 6.6 6.6 2.4-6.6 2.4L12 20.5l-2.4-6.6L3 11.5l6.6-2.4z"/>',
  };
  const ico = (n) => `<svg class="ic" viewBox="0 0 24 24" aria-hidden="true">${P[n] || ""}</svg>`;
  const hydrate = (root = document) => root.querySelectorAll("i[data-i]").forEach((el) => {
    const t = document.createElement("template");
    t.innerHTML = ico(el.dataset.i);
    const svg = t.content.firstChild;
    if (el.className) svg.classList.add(...el.className.split(" "));
    el.replaceWith(svg);
  });

  /* ---------------- helpers ---------------- */
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const store = {
    get(k, d) { try { const v = localStorage.getItem("recall." + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem("recall." + k, JSON.stringify(v)); } catch { /* storage unavailable */ } },
  };
  let toastTimer;
  function toast(msg, err = false) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.toggle("err", err);
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), 3800);
  }
  function ask(msg, yes = "Continue") {
    return new Promise((resolve) => {
      const d = $("#confirmModal");
      $("#confirmText").textContent = msg;
      $("#confirmYes").textContent = yes;
      const done = (v) => { d.close(); resolve(v); };
      $("#confirmYes").onclick = () => done(true);
      $("#confirmNo").onclick = () => done(false);
      d.oncancel = (e) => { e.preventDefault(); done(false); };
      d.showModal();
    });
  }
  const ago = (ts) => {
    const s = (Date.now() - ts) / 1000;
    if (s < 60) return "Just now";
    if (s < 3600) return `${Math.floor(s / 60)} min ago`;
    if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
    const d = Math.floor(s / 86400);
    return d === 1 ? "Yesterday" : `${d} days ago`;
  };
  const fmtTime = (sec) => `${Math.floor(sec / 60)}:${String(Math.floor(sec % 60)).padStart(2, "0")}`;
  const download = (name, text, type) => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type }));
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  };

  /* ---------------- state ---------------- */
  const S = {
    source: "topic",
    files: [],
    demo: false,
    status: null,
    settings: Object.assign({
      difficulty: "Medium", mode: "Practice", n_mcq: 5, n_short: 2, n_code: 0,
      language: "Python", timer: 15, engine: "auto", depth: "standard", use_web: true,
    }, store.get("settings", {})),
    quiz: null,     // active quiz session
    abort: null,
    timerId: null,
  };
  const saveSettings = () => store.set("settings", S.settings);
  const apiBase = () => (store.get("apiBase", "") || "").replace(/\/$/, "");
  async function api(path, opts = {}) {
    const res = await fetch(apiBase() + path, opts);
    let data;
    try { data = await res.json(); } catch { data = {}; }
    if (!res.ok) throw new Error(data.error || `Server error (${res.status})`);
    return data;
  }

  /* ---------------- views ---------------- */
  const VIEWS = ["home", "loading", "quiz", "results", "review", "history"];
  function show(view) {
    VIEWS.forEach((v) => { $("#view-" + v).hidden = v !== view; });
    $("#shell").classList.remove("nav-open");
    window.scrollTo({ top: 0, behavior: "smooth" });
    setNav(view === "history" ? "history" : view === "home" ? (S.source === "docs" ? "docs" : "home") : null);
    if (view !== "quiz") stopTimer();
  }
  function setNav(key) {
    $$(".nav a").forEach((a) => a.classList.toggle("active", a.dataset.nav === key));
  }

  /* ---------------- composer ---------------- */
  function setSource(src) {
    S.source = src;
    $$(".ctab").forEach((b) => b.classList.toggle("active", b.dataset.source === src));
    $$(".pane").forEach((p) => { p.hidden = p.dataset.pane !== src; });
    moveInk();
  }
  function moveInk() {
    const a = $(".ctab.active"), ink = $(".ctab-ink");
    if (!a) return;
    ink.style.width = a.offsetWidth + "px";
    ink.style.transform = `translateX(${a.offsetLeft - 4}px)`;
  }
  function syncControls() {
    const st = S.settings;
    $$(".seg").forEach((seg) => $$("button", seg).forEach((b) => b.classList.toggle("on", b.dataset.v === st[seg.dataset.setting])));
    $$(".stepper").forEach((s) => { $("output", s).textContent = st[s.dataset.k]; });
    $("#langSelect").value = st.language;
    $("#timerSelect").value = String(st.timer);
    $("#depthSelect").value = st.depth;
    $("#webToggle").checked = st.use_web;
    const parts = [];
    if (st.n_mcq) parts.push(`${st.n_mcq} MCQ`);
    if (st.n_short) parts.push(`${st.n_short} written`);
    if (st.n_code) parts.push(`${st.n_code} code`);
    $("#mixLabel").textContent = parts.join(" · ") || "No questions";
  }
  function buildSteppers() {
    $$(".stepper").forEach((s) => {
      s.innerHTML = '<button type="button" aria-label="Less">−</button><output></output><button type="button" aria-label="More">+</button>';
      const [minus, plus] = $$("button", s);
      const k = s.dataset.k, min = +s.dataset.min, max = +s.dataset.max;
      minus.onclick = () => { S.settings[k] = Math.max(min, S.settings[k] - 1); saveSettings(); syncControls(); };
      plus.onclick = () => { S.settings[k] = Math.min(max, S.settings[k] + 1); saveSettings(); syncControls(); };
    });
  }
  function toggleMix(open) {
    const pop = $("#mixPop"), btn = $("#mixBtn");
    const willOpen = open ?? pop.hidden;
    pop.hidden = !willOpen;
    btn.setAttribute("aria-expanded", String(willOpen));
  }
  function renderFiles() {
    $("#fileChips").innerHTML = S.files.map((f, i) =>
      `<span class="file-chip">${ico("file")}${esc(f.name)} <span class="muted">${(f.size / 1024).toFixed(0)} KB</span><button data-rm="${i}" aria-label="Remove ${esc(f.name)}">${ico("x")}</button></span>`).join("");
  }
  function addFiles(list) {
    const ok = /\.(pdf|docx|pptx|txt|md)$/i;
    let rejected = 0;
    [...list].forEach((f) => { if (ok.test(f.name)) S.files.push(f); else rejected++; });
    if (rejected) toast(`${rejected} file(s) skipped — use PDF, DOCX, PPTX, TXT or MD.`, true);
    renderFiles();
  }

  const SUGGESTIONS = ["Operating system scheduling", "DBMS normalization", "OSI model", "Dynamic programming", "Machine learning basics", "Photosynthesis"];
  function renderSuggestions() {
    $("#suggest").insertAdjacentHTML("beforeend", SUGGESTIONS.map((t) => `<button class="sugg" data-topic="${esc(t)}"><span class="dot"></span>${esc(t)}</button>`).join(""));
  }

  /* ---------------- generation ---------------- */
  const STEPS = {
    topic: ["Searching the web", "Reading the best sources", "Writing your questions", "Checking answers"],
    topicOffline: ["Understanding the topic", "Writing your questions", "Checking answers"],
    docs: ["Reading your documents", "Finding key ideas", "Writing your questions", "Checking answers"],
  };
  let stepTimer;
  function startLoading(kind, title) {
    $("#loadTitle").textContent = title;
    const steps = STEPS[kind];
    $("#loadSteps").innerHTML = steps.map((s) => `<li><span class="st"></span>${s}</li>`).join("");
    let i = 0;
    const lis = $$("#loadSteps li");
    const tick = () => {
      lis.forEach((li, j) => {
        li.className = j < i ? "done" : j === i ? "active" : "";
        $(".st", li).innerHTML = j < i ? ico("check") : "";
      });
      if (i < lis.length - 1) { i++; stepTimer = setTimeout(tick, 2600 + Math.random() * 2000); }
    };
    clearTimeout(stepTimer);
    tick();
    $("#generateBtn").classList.add("busy");
    show("loading");
  }
  function stopLoading() { clearTimeout(stepTimer); $("#generateBtn").classList.remove("busy"); }

  async function generate() {
    const st = S.settings;
    if (st.n_mcq + st.n_short + st.n_code === 0) { toast("Pick at least one question in the mix.", true); toggleMix(true); return; }

    let title, kind, request;
    if (S.source === "topic") {
      const topic = $("#topicInput").value.trim();
      if (topic.length < 2) { toast("Type a topic first — anything you want to learn.", true); $("#topicInput").focus(); return; }
      title = topic;
      kind = st.use_web ? "topic" : "topicOffline";
      request = () => api("/api/quiz/topic", {
        method: "POST", headers: { "Content-Type": "application/json" }, signal: S.abort.signal,
        body: JSON.stringify({ ...payloadSettings(), topic, use_web: st.use_web, depth: st.depth }),
      });
    } else {
      const text = $("#pasteInput").value;
      if (!S.files.length && text.trim().length < 80) { toast("Add a file or paste at least a few sentences of notes.", true); return; }
      title = S.files.length ? S.files.map((f) => f.name.replace(/\.[^.]+$/, "")).join(", ") : text.trim().slice(0, 48) + "…";
      kind = "docs";
      const fd = new FormData();
      S.files.forEach((f) => fd.append("files", f));
      fd.append("text", text);
      fd.append("settings", JSON.stringify(payloadSettings()));
      request = () => api("/api/quiz/document", { method: "POST", body: fd, signal: S.abort.signal });
    }

    S.abort = new AbortController();
    startLoading(kind, S.source === "topic" ? `Building a quiz on “${title}”` : "Building a quiz from your notes");
    try {
      let data;
      if (S.demo) {
        await new Promise((r) => setTimeout(r, 2200));
        data = { quiz: DEMO_QUIZ, sources: DEMO_SOURCES };
        title = "Sample: Binary search";
      } else {
        data = await request();
      }
      stopLoading();
      if (S.source === "topic" && st.use_web && !S.demo && data.web_used === false) {
        toast("Couldn't reach the web — questions are from the AI's own knowledge.");
      }
      startQuiz({
        quiz: data.quiz, title, source: S.source, sources: data.sources || [],
        difficulty: st.difficulty, mode: st.mode, timer: st.timer,
      });
    } catch (e) {
      stopLoading();
      show("home");
      if (e.name !== "AbortError") toast(e.message || "Something went wrong.", true);
    }
  }
  const payloadSettings = () => {
    const { difficulty, n_mcq, n_short, n_code, language, engine } = S.settings;
    return { difficulty, n_mcq, n_short, n_code, language, engine };
  };

  /* ---------------- quiz session ---------------- */
  const TYPE_LABEL = { mcq: "Multiple choice", short: "Written answer", coding: "Coding" };
  function flatten(quiz) {
    return ["mcq", "short", "coding"].flatMap((t) => (quiz[t] || []).map((q) => ({ ...q, type: t })));
  }
  function startQuiz({ quiz, title, source, sources, difficulty, mode, timer, items, historyId, retry = 0 }) {
    const qs = items || flatten(quiz);
    if (!qs.length) { toast("The AI returned no usable questions. Try again.", true); show("home"); return; }
    S.quiz = {
      id: historyId || "q" + Date.now(), quiz, title, source, sources: sources || [], difficulty, mode,
      timer: +timer || 15, items: qs, answers: {}, revealed: {}, grades: {}, code: {}, flagged: new Set(),
      i: 0, started: Date.now(), finished: null, retry,
    };
    $("#quizName").textContent = title + (retry ? ` · retry ${retry}` : "");
    $("#flagBtn").hidden = mode !== "Exam";
    show("quiz");
    if (mode === "Exam") startTimer();
    renderQuestion();
  }
  const Q = () => S.quiz;
  const correctText = (q) => q.options[q.answer_index];
  function status(i) {
    const q = Q().items[i], a = Q().answers[i];
    if (q.type !== "mcq") return String(a ?? "").trim() && a !== q.starter_code ? "open" : "skipped";
    return a == null ? "skipped" : a === correctText(q) ? "right" : "wrong";
  }

  function startTimer() {
    stopTimer();
    const el = $("#timer");
    el.hidden = false;
    const tick = () => {
      const left = Q().timer * 60 - (Date.now() - Q().started) / 1000;
      $("span", el).textContent = fmtTime(Math.max(0, left));
      el.classList.toggle("urgent", left < 60);
      if (left <= 0) { stopTimer(); toast("Time's up — submitting your exam."); finish(); }
    };
    tick();
    S.timerId = setInterval(tick, 500);
  }
  function stopTimer() { clearInterval(S.timerId); S.timerId = null; $("#timer").hidden = true; }

  function renderQuestion() {
    const z = Q(), i = z.i, q = z.items[i], n = z.items.length, practice = z.mode === "Practice";
    $("#quizMeta").textContent = `Question ${i + 1} of ${n} · ${z.difficulty} · ${z.mode}`;
    $("#progressBar").style.width = `${((i + 1) / n) * 100}%`;

    // navigation grid
    $("#qgrid").innerHTML = z.items.map((_, j) => {
      const s = status(j);
      let cls = j === i ? "current" : "";
      if (j !== i && s !== "skipped") cls = practice && z.revealed[j] && z.items[j].type === "mcq" ? s : "answered";
      if (z.flagged.has(j)) cls += " flagged";
      return `<button class="${cls}" data-jump="${j}" aria-label="Question ${j + 1}">${j + 1}</button>`;
    }).join("");

    let body = `<span class="qtype">${ico(q.type === "mcq" ? "list" : q.type === "short" ? "pen" : "code")}${TYPE_LABEL[q.type]}</span>
      <div class="qtext">${esc(q.question)}</div>`;

    if (q.type === "mcq") {
      const picked = z.answers[i], locked = practice && z.revealed[i];
      body += `<div class="options">${q.options.map((o, j) => {
        let cls = "opt", mark = "";
        if (locked) {
          if (j === q.answer_index) { cls += " correct"; mark = ico("check"); }
          else if (o === picked) { cls += " incorrect"; mark = ico("x"); }
        } else if (o === picked) cls += " picked";
        return `<button class="${cls}" data-opt="${j}" ${locked ? "disabled" : ""}><span class="letter">${"ABCD"[j]}</span><span>${esc(o)}</span><span class="mark">${mark}</span></button>`;
      }).join("")}</div>`;
      if (locked) {
        const ok = picked === correctText(q);
        body += `<div class="feedback ${ok ? "ok" : "bad"}"><b class="h">${ico(ok ? "check" : "x")}${ok ? "Correct!" : "Not quite."}</b>
          ${ok ? "" : `The answer is <b>${esc(correctText(q))}</b>. `}${esc(q.explanation || "")}
          ${q.source_quote ? `<div class="quote">“${esc(q.source_quote)}”</div>` : ""}</div>`;
      }
    } else if (q.type === "short") {
      const val = z.answers[i] ?? "";
      body += `<textarea class="answer-box" id="ansBox" placeholder="Write your answer in your own words…">${esc(val)}</textarea>`;
      if (practice) {
        body += `<div class="row-actions"><button class="btn primary sm" id="gradeBtn">${ico("target")}Check with AI</button>
          <button class="btn ghost sm" id="showModel">${ico("info")}Show model answer</button></div>`;
        body += renderGrade(i, q);
        if (z.revealed[i] === "model") body += `<div class="feedback info"><b class="h">Model answer</b>${esc(q.model_answer)}</div>`;
      }
    } else {
      const val = z.answers[i] ?? q.starter_code ?? "";
      body += `<textarea class="code-box" id="codeBox" spellcheck="false" placeholder="Write your ${esc(q.language || "code")} here…">${esc(val)}</textarea>`;
      const canRun = /^py/i.test(q.language || "python") && (q.test_cases || []).length;
      body += `<div class="row-actions">
        ${canRun ? `<button class="btn primary sm" id="runBtn">${ico("play")}Run tests</button>` : `<span class="muted" style="font-size:.85rem">Auto-testing supports Python; compare with the solution in review.</span>`}
        ${practice ? `<button class="btn ghost sm" id="showSol">${ico("info")}Show solution</button>` : ""}</div>`;
      body += renderTests(i);
      if (practice && z.revealed[i] === "solution") body += `<div class="feedback info"><b class="h">Solution</b><pre class="code">${esc(q.solution)}</pre>${q.explanation ? `<p>${esc(q.explanation)}</p>` : ""}</div>`;
    }
    const card = $("#qcard");
    card.innerHTML = body;
    card.style.animation = "none"; void card.offsetWidth; card.style.animation = "";

    const last = i === n - 1;
    $("#prevBtn").disabled = i === 0;
    $("#nextBtn").innerHTML = last ? `${z.mode === "Exam" ? "Submit exam" : "Finish"}${ico("check")}` : `Next${ico("arrowRight")}`;
    $("#flagBtn span").textContent = z.flagged.has(i) ? "Flagged" : "Flag";
    $("#flagBtn").classList.toggle("ok", z.flagged.has(i));
    wireQuestion(i, q);
  }

  function renderGrade(i, q) {
    const g = Q().grades[i];
    if (!g) return "";
    if (g.loading) return `<div class="feedback info"><b class="h">${ico("target")}Grading your answer…</b></div>`;
    const ok = (g.score ?? 0) >= 70;
    return `<div class="feedback ${ok ? "ok" : "bad"}"><b class="h">${ico(ok ? "check" : "info")}Score: ${g.score ?? 0}%</b>${esc(g.feedback || "")}
      ${(g.hits || []).length || (g.misses || []).length ? `<ul class="kp">${(g.hits || []).map((h) => `<li class="hit">${ico("check")}${esc(h)}</li>`).join("")}${(g.misses || []).map((m) => `<li class="miss">${ico("x")}${esc(m)}</li>`).join("")}</ul>` : ""}</div>`;
  }
  function renderTests(i) {
    const r = Q().code[i];
    if (!r) return "";
    if (r.loading) return `<div class="feedback info"><b class="h">${ico("play")}Running tests…</b></div>`;
    if (r.error) return `<div class="feedback bad"><b class="h">${ico("x")}Couldn't run</b>${esc(r.error)}</div>`;
    const all = r.passed === r.total;
    return `<div class="feedback ${all ? "ok" : "bad"}"><b class="h">${ico(all ? "check" : "x")}${all ? "All tests passed!" : `${r.passed}/${r.total} tests passed`}</b>
      <div class="tests">${(r.results || []).map((t, j) => `<div class="test ${t.passed ? "pass" : "fail"}"><div class="tl">${ico(t.passed ? "check" : "x")}Test ${j + 1}</div>input:    ${esc(t.input)}\nexpected: ${esc(t.expected)}\nactual:   ${esc(t.actual)}${t.error ? "\n" + esc(t.error) : ""}</div>`).join("")}</div></div>`;
  }

  function wireQuestion(i, q) {
    const z = Q();
    $$("[data-opt]").forEach((b) => b.onclick = () => pickOption(+b.dataset.opt));
    const ans = $("#ansBox");
    if (ans) ans.oninput = () => { z.answers[i] = ans.value; };
    const code = $("#codeBox");
    if (code) {
      code.oninput = () => { z.answers[i] = code.value; };
      code.onkeydown = (e) => {
        if (e.key === "Tab") {
          e.preventDefault();
          const s = code.selectionStart;
          code.setRangeText("    ", s, code.selectionEnd, "end");
          z.answers[i] = code.value;
        }
      };
    }
    const gb = $("#gradeBtn");
    if (gb) gb.onclick = () => gradeShort(i, q);
    const sm = $("#showModel");
    if (sm) sm.onclick = () => { z.revealed[i] = z.revealed[i] === "model" ? null : "model"; renderQuestion(); };
    const rb = $("#runBtn");
    if (rb) rb.onclick = () => runCode(i, q);
    const ss = $("#showSol");
    if (ss) ss.onclick = () => { z.revealed[i] = z.revealed[i] === "solution" ? null : "solution"; renderQuestion(); };
  }

  function pickOption(j) {
    const z = Q(), i = z.i, q = z.items[i];
    if (q.type !== "mcq" || (z.mode === "Practice" && z.revealed[i])) return;
    z.answers[i] = q.options[j];
    if (z.mode === "Practice") z.revealed[i] = true;
    renderQuestion();
  }

  async function gradeShort(i, q) {
    const z = Q(), answer = (z.answers[i] || "").trim();
    if (!answer) { toast("Write an answer first.", true); return; }
    z.grades[i] = { loading: true };
    renderQuestion();
    try {
      z.grades[i] = S.demo ? demoGrade(answer, q) : await api("/api/grade", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer, model_answer: q.model_answer, key_points: q.key_points || [], engine: S.settings.engine }),
      });
    } catch (e) {
      z.grades[i] = { score: 0, hits: [], misses: q.key_points || [], feedback: "Grading failed: " + e.message };
    }
    if (Q() === z && z.i === i) renderQuestion();
  }

  async function runCode(i, q) {
    const z = Q(), code = z.answers[i] ?? q.starter_code ?? "";
    if (!code.trim()) { toast("Write some code first.", true); return; }
    if (S.demo) { z.code[i] = { error: "Code runs on your local server. Start it with: python -m recall.server" }; renderQuestion(); return; }
    z.code[i] = { loading: true };
    renderQuestion();
    try {
      z.code[i] = await api("/api/run", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, test_cases: q.test_cases, language: q.language || "python" }) });
    } catch (e) { z.code[i] = { error: e.message }; }
    if (Q() === z && z.i === i) renderQuestion();
  }

  function go(delta) {
    const z = Q(), n = z.items.length;
    if (delta > 0 && z.i === n - 1) return submit();
    z.i = Math.max(0, Math.min(n - 1, z.i + delta));
    renderQuestion();
  }
  async function submit() {
    const z = Q();
    const left = z.items.filter((_, j) => status(j) === "skipped").length;
    if (left && !(await ask(`${left} question${left > 1 ? "s are" : " is"} unanswered. Submit anyway?`, "Submit"))) return;
    finish();
  }

  /* ---------------- results ---------------- */
  function tally() {
    const z = Q();
    const mcq = z.items.map((q, j) => [q, status(j)]).filter(([q]) => q.type === "mcq");
    const right = mcq.filter(([, s]) => s === "right").length;
    return { right, total: mcq.length };
  }
  function finish() {
    const z = Q();
    z.finished = Date.now();
    stopTimer();
    saveHistory();
    renderResults();
    show("results");
  }
  function renderResults() {
    const z = Q(), { right, total } = tally();
    const secs = Math.round((z.finished - z.started) / 1000);
    const pct = total ? Math.round((100 * right) / total) : null;
    const head = pct == null ? "Quiz complete." : pct >= 90 ? "Outstanding recall." : pct >= 75 ? "Strong work." : pct >= 50 ? "Getting there." : "Worth another pass.";
    const sub = pct == null ? "No multiple-choice questions to auto-score — compare your answers with the model answers in review."
      : `You got ${right} of ${total} multiple-choice questions right${z.retry ? ` in retry round ${z.retry}` : ""}.`;
    const wrong = z.items.filter((q, j) => q.type === "mcq" && status(j) !== "right");
    const C = 2 * Math.PI * 88;
    const written = z.items.filter((q) => q.type !== "mcq").length;

    $("#view-results").innerHTML = `
      <div class="res-top glass">
        <div class="ring">
          <svg viewBox="0 0 200 200"><defs><linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#839ff8"/><stop offset=".5" stop-color="#839ff8"/><stop offset="1" stop-color="#3542dc"/></linearGradient></defs>
            <circle class="track" cx="100" cy="100" r="88" fill="none" stroke-width="14"/>
            <circle class="val" id="ringVal" cx="100" cy="100" r="88" fill="none" stroke-width="14" stroke-dasharray="${C}" stroke-dashoffset="${C}"/></svg>
          <div class="center"><div class="pct">${pct == null ? "—" : pct + "%"}</div><div class="sub">${total ? `${right} / ${total} correct` : "self-check"}</div></div>
        </div>
        <div class="res-head"><div class="eyebrow">${esc(z.difficulty)} · ${esc(z.mode)} · ${esc(z.title)}</div><h1>${head}</h1><p>${sub}</p></div>
      </div>
      <div class="metrics">
        <div class="metric glass"><div class="v">${pct == null ? "—" : pct + "%"}</div><div class="l">Score</div></div>
        <div class="metric glass"><div class="v">${right}/${total}</div><div class="l">MCQ correct</div></div>
        <div class="metric glass"><div class="v">${written}</div><div class="l">Written / code</div></div>
        <div class="metric glass"><div class="v">${fmtTime(secs)}</div><div class="l">Time taken</div></div>
      </div>
      <div class="strip" aria-label="Result per question">${z.items.map((_, j) => `<i class="${status(j)}" title="Question ${j + 1}"></i>`).join("")}</div>
      <div class="actions">
        <button class="btn primary" data-act="retry" ${wrong.length ? "" : "disabled"}>${ico("target")}Retry ${wrong.length} mistake${wrong.length === 1 ? "" : "s"}</button>
        <button class="btn" data-act="review-wrong" ${wrong.length ? "" : "disabled"}>${ico("x")}Review mistakes</button>
        <button class="btn" data-act="review-all">${ico("list")}Review all</button>
        <button class="btn" data-act="retake">${ico("replay")}Retake quiz</button>
        ${S.demo ? "" : `<button class="btn" data-act="json">${ico("download")}Download JSON</button>
        <button class="btn" data-act="md">${ico("download")}Download Markdown</button>`}
      </div>
      <div style="display:flex;justify-content:center;margin-top:16px"><button class="btn ghost" data-act="new">${ico("plus")}New quiz</button></div>
      ${renderSources(z.sources)}`;
    requestAnimationFrame(() => setTimeout(() => {
      const el = $("#ringVal");
      if (el) el.style.strokeDashoffset = C * (1 - (pct ?? 100) / 100);
    }, 60));
  }
  function renderSources(src) {
    if (!src || !src.length) return "";
    return `<div class="sources glass"><div class="panel-title" style="margin:0">${ico("globe")} Sources used</div><ul>${src.map((s) =>
      `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${ico("link")}<span>${esc(s.title)}</span><span class="site">${esc(s.site || "")}</span></a></li>`).join("")}</ul></div>`;
  }

  function resultsAction(act) {
    const z = Q();
    if (act === "retry") {
      const items = z.items.filter((q, j) => q.type === "mcq" && status(j) !== "right");
      startQuiz({ ...z, mode: "Practice", items, retry: (z.retry || 0) + 1, historyId: null });
    } else if (act === "review-wrong" || act === "review-all") {
      renderReview(act === "review-wrong");
      show("review");
    } else if (act === "retake") {
      startQuiz({ ...z, items: null, retry: 0, historyId: null });
    } else if (act === "json") {
      download(slug(z.title) + ".json", JSON.stringify(z.quiz, null, 2), "application/json");
    } else if (act === "md") {
      download(slug(z.title) + ".md", toMarkdown(z), "text/markdown");
    } else if (act === "new") {
      show("home");
    }
  }
  const slug = (s) => (s || "quiz").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40) || "quiz";
  function toMarkdown(z) {
    const out = [`# ${z.title} — Quiz (${z.difficulty})`, ""];
    const qz = z.quiz;
    (qz.mcq || []).forEach((q, i) => {
      out.push(`**Q${i + 1}. ${q.question}**`, ...q.options.map((o, j) => `- ${"ABCD"[j]}. ${o}`), "", `Answer: ${"ABCD"[q.answer_index]}. ${q.explanation || ""}`, "");
    });
    (qz.short || []).forEach((q, i) => out.push(`**Written ${i + 1}. ${q.question}**`, "", `Model answer: ${q.model_answer}`, ""));
    (qz.coding || []).forEach((q, i) => out.push(`**Coding ${i + 1}. ${q.question}**`, "", "```" + (q.language || "python").toLowerCase(), q.solution, "```", ""));
    if (z.sources.length) out.push("## Sources", ...z.sources.map((s) => `- [${s.title}](${s.url})`));
    return out.join("\n");
  }

  /* ---------------- review ---------------- */
  function renderReview(onlyWrong) {
    const z = Q();
    const L = { right: ["check", "Correct"], wrong: ["x", "Incorrect"], open: ["pen", "Your answer"], skipped: ["minus", "Skipped"] };
    const cards = z.items.map((q, i) => {
      const s = status(i);
      if (onlyWrong && !(q.type === "mcq" && s !== "right")) return "";
      const a = z.answers[i];
      let b = `<span class="chip ${s}">${ico(L[s][0])}${L[s][1]}</span><div class="qtext">${i + 1}. ${esc(q.question)}</div>`;
      if (q.type === "mcq") {
        b += `<span class="k">Your answer</span><p>${a ? esc(a) : "—"}</p>`;
        if (s !== "right") b += `<span class="k">Correct answer</span><p style="color:var(--ok)">${esc(correctText(q))}</p>`;
        if (q.explanation) b += `<span class="k">Why</span><p>${esc(q.explanation)}</p>`;
        if (q.source_quote) b += `<div class="quote">“${esc(q.source_quote)}”</div>`;
      } else if (q.type === "short") {
        b += `<span class="k">Your answer</span><p>${esc(a || "—")}</p><span class="k">Model answer</span><p>${esc(q.model_answer)}</p>`;
        if ((q.key_points || []).length) b += `<span class="k">Key points</span><ul class="kp">${q.key_points.map((k) => `<li>${ico("spark")}${esc(k)}</li>`).join("")}</ul>`;
        if (z.grades[i] && !z.grades[i].loading) b += `<span class="k">AI score</span><p><b>${z.grades[i].score}%</b> — ${esc(z.grades[i].feedback || "")}</p>`;
      } else {
        b += `<span class="k">Your code</span><pre class="code">${esc(a || "—")}</pre><span class="k">Solution</span><pre class="code">${esc(q.solution)}</pre>`;
        if (q.explanation) b += `<p>${esc(q.explanation)}</p>`;
        const r = z.code[i];
        if (r && r.total != null) b += `<span class="k">Tests</span><p>${r.passed}/${r.total} passed</p>`;
      }
      return `<div class="rev-card glass">${b}</div>`;
    }).join("");
    $("#view-review").innerHTML = `<div class="rev-head"><button class="btn ghost sm" data-act="back">${ico("arrowLeft")}Results</button><h2>${onlyWrong ? "Your mistakes" : "All questions"}</h2></div>
      ${cards || `<div class="empty-state">${ico("check")}<p>Nothing to review — every multiple-choice answer was correct.</p></div>`}`;
  }

  /* ---------------- history & stats ---------------- */
  function saveHistory() {
    const z = Q();
    if (z.retry) return; // only store original attempts
    const { right, total } = tally();
    const hist = store.get("history", []).filter((h) => h.id !== z.id);
    hist.unshift({
      id: z.id, title: z.title, source: z.source, difficulty: z.difficulty, mode: z.mode, timer: z.timer,
      date: Date.now(), right, total, count: z.items.length, quiz: z.quiz, sources: z.sources,
    });
    store.set("history", hist.slice(0, 40));
    renderSidebar();
    renderStats();
  }
  function renderSidebar(filter = "") {
    const f = filter.toLowerCase();
    const hist = store.get("history", []).filter((h) => !f || h.title.toLowerCase().includes(f)).slice(0, 8);
    $("#recentList").innerHTML = hist.length ? hist.map((h) => `<li><button data-hist="${esc(h.id)}"><span class="r-title">${esc(h.title)}</span><span class="r-sub">${ago(h.date)}${h.total ? ` · ${Math.round(100 * h.right / h.total)}%` : ""}</span></button></li>`).join("")
      : `<li class="empty">${f ? "No matches." : "Your quizzes will appear here."}</li>`;
  }
  function renderHistory() {
    const hist = store.get("history", []);
    $("#view-history").innerHTML = `<div class="rev-head"><h2>History</h2>${hist.length ? `<button class="btn ghost sm" data-act="clear">${ico("trash")}Clear</button>` : ""}</div>` +
      (hist.length ? `<div class="hist-list">${hist.map((h) => `<div class="hist-item glass"><span class="hi-icon">${ico(h.source === "docs" ? "file" : "globe")}</span>
        <div class="hi-main"><div class="hi-title">${esc(h.title)}</div><div class="hi-sub">${ago(h.date)} · ${h.count} questions · ${esc(h.difficulty)} · ${esc(h.mode)}</div></div>
        <div class="hi-score">${h.total ? Math.round(100 * h.right / h.total) + "%" : "—"}</div>
        <button class="btn sm" data-hist="${esc(h.id)}">${ico("replay")}Retake</button></div>`).join("")}</div>`
        : `<div class="empty-state">${ico("clock")}<p>No quizzes yet. Pick a topic on the home screen to start.</p></div>`);
  }
  function retakeFromHistory(id) {
    const h = store.get("history", []).find((x) => x.id === id);
    if (!h) return;
    startQuiz({ quiz: h.quiz, title: h.title, source: h.source, sources: h.sources, difficulty: h.difficulty, mode: h.mode, timer: h.timer, historyId: h.id });
  }
  function renderStats() {
    const hist = store.get("history", []);
    const scored = hist.filter((h) => h.total);
    $("#statQuizzes").textContent = hist.length;
    $("#statQs").textContent = hist.reduce((a, h) => a + (h.count || 0), 0);
    $("#statAvg").textContent = scored.length ? Math.round(scored.reduce((a, h) => a + (100 * h.right) / h.total, 0) / scored.length) + "%" : "—";
    const pts = scored.slice(0, 12).reverse().map((h) => (100 * h.right) / h.total);
    const svg = $("#sparkline");
    const data = pts.length >= 2 ? pts : [40, 55, 48, 62, 58, 70, 66, 78];
    const w = 260, hgt = 50, step = w / (data.length - 1);
    const xy = data.map((v, i) => [i * step, hgt - (v / 100) * (hgt - 6) + 2]);
    const line = xy.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
    svg.innerHTML = `<defs><linearGradient id="spk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#839ff8" stop-opacity=".45"/><stop offset="1" stop-color="#839ff8" stop-opacity="0"/></linearGradient></defs>
      <path d="${line} L${w},56 L0,56 Z" fill="url(#spk)"/><path d="${line}" fill="none" stroke="#839ff8" stroke-width="2" style="filter:drop-shadow(0 0 4px #4f6ef7)" opacity="${pts.length >= 2 ? 1 : .35}"/>`;
  }

  /* ---------------- server status / engines ---------------- */
  async function loadStatus() {
    try {
      S.status = await api("/api/status");
      S.demo = false;
    } catch {
      S.demo = true;
      S.status = { engines: [{ id: "demo", label: "Demo (offline sample)" }], capabilities: { web_research: false, documents: false, code_runner: false, ai_grading: true } };
    }
    $("#demoBanner").hidden = !S.demo;
    const opts = [{ id: "auto", label: "Auto (best available)" }, ...S.status.engines.filter((e) => e.id !== "demo")];
    const html = (S.demo ? S.status.engines : opts).map((e) => `<option value="${esc(e.id)}">${esc(e.label)}</option>`).join("");
    $("#engineSelect").innerHTML = html;
    $("#engineSelect2").innerHTML = html;
    if (!S.demo && opts.some((o) => o.id === S.settings.engine)) $("#engineSelect").value = S.settings.engine;
    updateEngineCard();
    $$("[data-cap]").forEach((el) => el.classList.toggle("off", !S.status.capabilities[el.dataset.cap]));
    if (S.status.capabilities.tavily) $("#tavilyTag").textContent = ", Tavily";
  }
  function updateEngineCard() {
    const sel = $("#engineSelect");
    const label = sel.options[sel.selectedIndex]?.text || "AI Engine";
    const m = sel.value === "auto" ? ["", "Auto engine", "Uses Groq Cloud when your key is set, otherwise your local Ollama model."]
      : label.match(/^([^(]+)\(([^)]+)\)/);
    $("#engineName").textContent = m ? m[1].trim() : label.split(" (")[0];
    $("#engineDesc").textContent = S.demo ? "Start the local server to generate real quizzes."
      : m ? m[2] : "Picks Groq Cloud when a key is set, otherwise your local Ollama model.";
  }

  /* ---------------- demo content (used only when the server is offline) ---------------- */
  const DEMO_QUIZ = {
    mcq: [
      { question: "What is the time complexity of binary search on a sorted array of n elements?", options: ["O(n)", "O(log n)", "O(n log n)", "O(1)"], answer_index: 1, explanation: "Each comparison halves the remaining search space, so at most about log₂ n steps are needed.", source_quote: "Binary search runs in logarithmic time in the worst case, making O(log n) comparisons." },
      { question: "Which precondition must hold before binary search can be applied?", options: ["The array must contain no duplicates", "The array must be sorted", "The array length must be a power of two", "The array must be stored in a linked list"], answer_index: 1, explanation: "Binary search relies on ordering to discard half of the elements after each comparison.", source_quote: "Binary search compares the target value to the middle element of a sorted array." },
      { question: "In the expression mid = (low + high) / 2, what problem can occur in languages with fixed-size integers?", options: ["Division by zero", "Integer overflow when low + high is very large", "Floating-point rounding errors", "Stack overflow"], answer_index: 1, explanation: "low + high can exceed the maximum int; mid = low + (high - low) / 2 avoids this.", source_quote: "A common bug is overflow in the computation of the midpoint." },
      { question: "Searching for 23 in [2, 5, 8, 12, 16, 23, 38, 56, 72, 91], which element is compared first (using floor of the middle index)?", options: ["16", "23", "12", "38"], answer_index: 0, explanation: "Indices 0–9 give mid = 4, so the first comparison is with arr[4] = 16.", source_quote: "" },
      { question: "What does binary search return when the target is not present (classic version)?", options: ["The middle index", "The last index checked", "An indication of absence, such as -1", "The index of the largest element"], answer_index: 2, explanation: "When low passes high, the interval is empty and the search reports that the value is absent.", source_quote: "If the search ends with the remaining half being empty, the target is not in the array." },
    ],
    short: [
      { question: "Explain why binary search is faster than linear search on large sorted arrays.", model_answer: "Linear search may check every element (O(n)), while binary search halves the remaining range with each comparison (O(log n)), so for a million elements it needs about 20 comparisons instead of up to a million.", key_points: ["halves the search space", "O(log n) vs O(n)", "requires sorted data"] },
    ],
    coding: [],
  };
  const DEMO_SOURCES = [
    { title: "Binary search", url: "https://en.wikipedia.org/wiki/Binary_search", site: "wikipedia.org" },
  ];
  function demoGrade(answer, q) {
    const a = answer.toLowerCase();
    const hits = [], misses = [];
    (q.key_points || []).forEach((k) => {
      const words = k.toLowerCase().split(/[^a-z0-9()]+/).filter((w) => w.length > 2);
      (words.some((w) => a.includes(w)) ? hits : misses).push(k);
    });
    const score = q.key_points?.length ? Math.round((100 * hits.length) / q.key_points.length) : 50;
    return { score, hits, misses, feedback: "Demo grading checks key words only — the real server uses AI to judge your answer." };
  }

  /* ---------------- events ---------------- */
  function presets(p) {
    show("home");
    if (p === "topic" || p === "home") { setSource("topic"); $("#topicInput").focus(); }
    if (p === "docs") { setSource("docs"); }
    if (p === "exam") { S.settings.mode = "Exam"; saveSettings(); syncControls(); toast(`Exam mode on — ${S.settings.timer} min timer. Change it under the mix button.`); $(S.source === "topic" ? "#topicInput" : "#pasteInput").focus(); }
    if (p === "code") { S.settings.n_code = Math.max(2, S.settings.n_code); S.settings.language = "Python"; saveSettings(); syncControls(); setSource("topic"); toast("Coding questions added (Python, with live tests)."); $("#topicInput").focus(); }
    setNav(p === "docs" ? "docs" : p === "topic" ? "topic" : "home");
  }

  function bind() {
    // nav
    document.addEventListener("click", async (e) => {
      const nav = e.target.closest("[data-nav]");
      if (nav) {
        e.preventDefault();
        const k = nav.dataset.nav;
        if (S.quiz && !$("#view-quiz").hidden && k !== "settings" && !(await ask("Leave this quiz? Your progress will be lost.", "Leave"))) return;
        if (k === "history") { renderHistory(); show("history"); }
        else if (k === "settings") openSettings();
        else presets(k);
        return;
      }
      const hist = e.target.closest("[data-hist]");
      if (hist) { retakeFromHistory(hist.dataset.hist); return; }
      const act = e.target.closest("[data-act]");
      if (act) {
        if (act.dataset.act === "back") { show("results"); return; }
        if (act.dataset.act === "clear") { if (await ask("Delete all quiz history?", "Delete")) { store.set("history", []); renderHistory(); renderSidebar(); renderStats(); } return; }
        resultsAction(act.dataset.act);
        return;
      }
      const jump = e.target.closest("[data-jump]");
      if (jump) { Q().i = +jump.dataset.jump; renderQuestion(); return; }
      const sug = e.target.closest("[data-topic]");
      if (sug) { setSource("topic"); $("#topicInput").value = sug.dataset.topic; $("#topicInput").focus(); return; }
      const pre = e.target.closest("[data-preset]");
      if (pre) { presets(pre.dataset.preset); return; }
      const rm = e.target.closest("[data-rm]");
      if (rm) { S.files.splice(+rm.dataset.rm, 1); renderFiles(); return; }
      if (!$("#mixPop").hidden && !e.target.closest("#mixPop") && !e.target.closest("#mixBtn")) toggleMix(false);
    });

    $$(".ctab").forEach((b) => b.onclick = () => { setSource(b.dataset.source); setNav(b.dataset.source === "docs" ? "docs" : "topic"); });
    $$(".seg").forEach((seg) => seg.onclick = (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      S.settings[seg.dataset.setting] = b.dataset.v;
      saveSettings(); syncControls();
    });
    $("#mixBtn").onclick = () => toggleMix();
    $("#mixDone").onclick = () => toggleMix(false);
    $("#langSelect").onchange = (e) => { S.settings.language = e.target.value; saveSettings(); };
    $("#timerSelect").onchange = (e) => { S.settings.timer = +e.target.value; saveSettings(); };
    $("#depthSelect").onchange = (e) => { S.settings.depth = e.target.value; saveSettings(); };
    $("#webToggle").onchange = (e) => { S.settings.use_web = e.target.checked; saveSettings(); };
    $("#engineSelect").onchange = (e) => { S.settings.engine = e.target.value; saveSettings(); updateEngineCard(); };

    // files
    const dz = $("#dropzone"), fi = $("#fileInput");
    dz.onclick = () => fi.click();
    dz.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fi.click(); } };
    fi.onchange = () => { addFiles(fi.files); fi.value = ""; };
    ["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("over"); }));
    ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("over"); }));
    dz.addEventListener("drop", (e) => addFiles(e.dataTransfer.files));
    $("#composer").addEventListener("dragover", (e) => { e.preventDefault(); if (S.source !== "docs") setSource("docs"); });
    $("#composer").addEventListener("drop", (e) => { if (!e.target.closest("#dropzone")) { e.preventDefault(); addFiles(e.dataTransfer.files); } });
    $("#attachBtn").onclick = () => { setSource("docs"); setNav("docs"); fi.click(); };

    // generate
    $("#generateBtn").onclick = generate;
    $("#topicInput").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); generate(); } });
    $("#cancelLoad").onclick = () => { S.abort?.abort(); stopLoading(); show("home"); };

    // quiz nav
    $("#prevBtn").onclick = () => go(-1);
    $("#nextBtn").onclick = () => go(1);
    $("#flagBtn").onclick = () => { const z = Q(); z.flagged.has(z.i) ? z.flagged.delete(z.i) : z.flagged.add(z.i); renderQuestion(); };
    $("#exitQuiz").onclick = async () => { if (await ask("Exit this quiz? Your progress will be lost.", "Exit")) { stopTimer(); show("home"); } };

    // keyboard
    document.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); $("#searchInput").focus(); return; }
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && !$("#view-home").hidden) { e.preventDefault(); generate(); return; }
      if ($("#view-quiz").hidden || !Q()) return;
      const typing = /TEXTAREA|INPUT|SELECT/.test(document.activeElement?.tagName);
      if (typing) return;
      const q = Q().items[Q().i];
      const k = e.key.toLowerCase();
      if (q.type === "mcq" && ["1", "2", "3", "4", "a", "b", "c", "d"].includes(k)) { pickOption("1234".includes(k) ? +k - 1 : "abcd".indexOf(k)); }
      else if (e.key === "ArrowRight" || e.key === "Enter") { e.preventDefault(); go(1); }
      else if (e.key === "ArrowLeft") go(-1);
    });

    // search filters recent quizzes
    $("#searchInput").oninput = (e) => renderSidebar(e.target.value);
    $("#searchInput").onkeydown = (e) => { if (e.key === "Enter") { renderHistory(); show("history"); } };

    // mobile menu
    $("#burger").onclick = () => $("#shell").classList.toggle("nav-open");
    $("#avatarBtn").onclick = openSettings;
    $("#saveSettings").onclick = () => {
      const name = $("#nameInput").value.trim();
      store.set("name", name);
      store.set("apiBase", $("#apiInput").value.trim());
      S.settings.engine = $("#engineSelect2").value;
      saveSettings();
      setAvatar();
      loadStatus();
    };
    $("#clearHistory").onclick = async () => { $("#settingsModal").close(); if (await ask("Delete all quiz history?", "Delete")) { store.set("history", []); renderSidebar(); renderStats(); toast("History cleared."); } };
    window.addEventListener("resize", moveInk);
  }
  function openSettings() {
    $("#nameInput").value = store.get("name", "");
    $("#apiInput").value = store.get("apiBase", "");
    $("#engineSelect2").value = $("#engineSelect").value;
    $("#settingsModal").showModal();
  }
  function setAvatar() {
    const n = store.get("name", "") || "Deepjyoti";
    $("#avatarInitial").textContent = n.trim()[0].toUpperCase();
  }

  /* ---------------- boot ---------------- */
  hydrate();
  buildSteppers();
  renderSuggestions();
  syncControls();
  setSource("topic");
  setAvatar();
  renderSidebar();
  renderStats();
  bind();
  loadStatus();
  requestAnimationFrame(moveInk);
})();
