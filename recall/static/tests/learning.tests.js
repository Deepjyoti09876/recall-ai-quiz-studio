/* Shared test body: runs in the browser (learning.test.html) and in Node (run_node.js). */
function runLearningTests(L, check) {
  const fresh = () => { L._setState(L.empty()); };
  const near = (a, b, e = 1e-6) => Math.abs(a - b) < e;

  // --- BKT
  let p = 0.3;
  check("BKT: correct raises mastery", L.bktUpdate(p, true, null, "mcq") > p);
  check("BKT: wrong lowers mastery", L.bktUpdate(p, false, null, "mcq") < p);
  check("BKT: sure+wrong drops more than guess+wrong", L.bktUpdate(0.6, false, "sure", "mcq") < L.bktUpdate(0.6, false, "guess", "mcq"));
  let q = 0.3; for (let i = 0; i < 10; i++) q = L.bktUpdate(q, false, "guess", "mcq");
  check("BKT: 10 guess+wrong never inflate mastery", q < 0.3, q);
  check("BKT: stays in [0.02, 0.99]", (() => { let a = 0.5; for (let i = 0; i < 80; i++) a = L.bktUpdate(a, true, "sure", "coding"); let b = 0.5; for (let i = 0; i < 80; i++) b = L.bktUpdate(b, false, "sure", "coding"); return a <= 0.99 && b >= 0.02; })());
  check("BKT: correct retry gains less than first try", L.bktUpdate(0.3, true, null, "mcq", "retry") < L.bktUpdate(0.3, true, null, "mcq", "quiz"));

  // --- SM-2
  const now = 1000000;
  const c = { ef: 2.5, interval: 0, reps: 0, lapses: 0, due: now, last: now };
  L.sm2Update(c, true, "sure", now); const i1 = c.interval;
  L.sm2Update(c, true, "sure", now); const i2 = c.interval;
  L.sm2Update(c, true, "sure", now); const i3 = c.interval;
  check("SM-2: intervals 1, 6, 16", i1 === 1 && i2 === 6 && i3 === 16, [i1, i2, i3]);
  check("SM-2: ef 2.8 after three sure answers", near(c.ef, 2.8, 1e-9), c.ef);
  L.sm2Update(c, false, "sure", now);
  check("SM-2: sure+wrong resets, lapses, due now", c.reps === 0 && c.interval === 1 && c.lapses === 1 && c.due === now);
  check("SM-2: ef floor 1.3", (() => { const d = { ef: 1.31, interval: 1, reps: 0, lapses: 0, due: 0, last: 0 }; for (let i = 0; i < 5; i++) L.sm2Update(d, false, "sure", now); return d.ef >= 1.3; })());

  // --- ids
  check("qid stable across whitespace/case", L.qid({ type: "mcq", question: "What  is X?" }) === L.qid({ type: "mcq", question: " what is x? " }));

  // --- graph
  fresh();
  L.mergeGraph([{ name: "A", prereqs: ["B"] }, { name: "B", prereqs: ["C"] }, { name: "C", prereqs: ["A"] }], "t");
  const edges = L.state().graph.edges;
  check("graph: cycle edge rejected", edges.length === 2 && !edges.some(([a, b]) => a === "a" && b === "c"), edges);
  fresh();
  L.mergeGraph([{ name: "Big O", prereqs: [] }, { name: "big  o", prereqs: [] }]);
  check("graph: names dedupe by normalised key", Object.keys(L.state().concepts).length === 1);

  // --- recording + recommend (root cause first)
  fresh();
  L.mergeGraph([{ name: "Pointers", prereqs: ["Memory"] }, { name: "Memory", prereqs: [] }], "t");
  const item = { type: "mcq", question: "Q1?", options: ["a", "b", "c", "d"], answer_index: 0, concept: "Pointers", misconceptions: [null, "thinks b", null, null] };
  for (let i = 0; i < 3; i++) L.recordAttempt({ item, correct: false, conf: "sure", misc: "thinks b", kind: "quiz" });
  const rec = L.recommend();
  check("recommend: untried prerequisite before weak concept", rec.concepts[0] === "Memory", rec);
  check("recordAttempt: card stored with item snapshot", L.state().cards[L.qid(item)].item.options.length === 4);
  check("recordAttempt: sure+wrong card due now", L.dueCards().length === 1);
  L.recordAttempt({ item, correct: true, conf: null, kind: "retry" });
  check("retry does not touch SM-2", L.state().cards[L.qid(item)].lapses === 3);
  check("misconception log counts repeats", L.weakMisconceptions()[0].count === 3);
  const cal = L.calibration(L.state().attempts);
  check("calibration: blind-spot quadrant counted", cal.quads.blind === 3 && cal.brier > 0.5, cal);

  // --- caps
  fresh();
  for (let i = 0; i < 700; i++) L.recordAttempt({ item: { type: "mcq", question: "Q" + i, concept: "C" + (i % 5), options: ["a", "b", "c", "d"], answer_index: 0 }, correct: i % 2 === 0, kind: "quiz" });
  L.flush();
  const st = L.state();
  check("caps: attempts <= 600 and cards <= 300", st.attempts.length <= 600 && Object.keys(st.cards).length <= 300, [st.attempts.length, Object.keys(st.cards).length]);

  // --- corrupt storage -> backup
  localStorage.setItem(L.KEY, "{not json");
  L._setState(null); L.load();
  check("corrupt state backed up and reset", localStorage.getItem(L.KEY + ".bak") === "{not json" && Object.keys(L.state().cards).length === 0);

  // --- normalizeQuiz
  const nq = L.normalizeQuiz({ mcq: [{ question: "x", options: ["a", "b", "c", "d"], answer_index: 2 }] });
  check("normalizeQuiz: default concept + misconceptions", nq.mcq[0].concept === "General" && nq.mcq[0].misconceptions[2] === null && nq.concepts[0].name === "General");
}
if (typeof module !== "undefined") module.exports = runLearningTests;
