"""Measure the quality of generated quizzes and write the numbers the report needs.

    python scripts/evaluate.py                  # real run: needs a working GROQ_API_KEY or local Ollama
    python scripts/evaluate.py --runs 3 --pause 25
    python scripts/evaluate.py --stub           # canned quizzes, checks the script itself (no model, no network)

Writes report/eval/results.csv (one row per quiz), summary.md and summary.tex.
Every figure comes from the runs: nothing is estimated.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from recall import quiz_engine as qe  # noqa: E402

TOPICS = [
    ("Operating system scheduling", "Easy"),
    ("DBMS normalization", "Medium"),
    ("Dynamic programming", "Hard"),
    ("TCP versus UDP", "Medium"),
    ("Binary search trees", "Easy"),
    ("Deadlock in operating systems", "Hard"),
]
N_MCQ, N_SHORT = 5, 2
FIELDS = ["topic", "difficulty", "ok", "seconds", "mcq", "short", "concepts", "with_concept", "mcq_with_misconceptions",
          "with_hints", "bloom_levels", "verified", "partial", "unsupported", "duplicates", "answer_positions_before",
          "answer_positions_after", "error"]


def _norm(s: str) -> str:
    return re.sub(r"\W+", " ", (s or "").lower()).strip()


def measure(topic: str, difficulty: str, result: dict, seconds: float, before_positions: list[int]) -> dict:
    """Turn one generated quiz into a flat row of measurements."""
    quiz = result["quiz"]
    qs = quiz.get("mcq", []) + quiz.get("short", []) + quiz.get("coding", [])
    mcq = quiz.get("mcq", [])
    ground = (result.get("context") or {}).get("grounding") or {}
    norms = [_norm(q.get("question", "")) for q in qs]
    return {
        "topic": topic, "difficulty": difficulty, "ok": 1, "seconds": round(seconds, 1),
        "mcq": len(mcq), "short": len(quiz.get("short", [])), "concepts": len(quiz.get("concepts", [])),
        "with_concept": sum(1 for q in qs if q.get("concept") and q["concept"] != "General"),
        "mcq_with_misconceptions": sum(1 for q in mcq if sum(1 for m in q.get("misconceptions", []) if m) >= 3),
        "with_hints": sum(1 for q in mcq + quiz.get("short", []) if q.get("hints")),
        "bloom_levels": "|".join(q.get("bloom", "") for q in qs),
        "verified": ground.get("verified", 0), "partial": ground.get("partial", 0), "unsupported": ground.get("unsupported", 0),
        "duplicates": len(norms) - len(set(norms)),
        "answer_positions_before": "".join(map(str, before_positions)),
        "answer_positions_after": "".join(str(q["answer_index"]) for q in mcq), "error": "",
    }


def summarise(rows: list[dict]) -> dict:
    """Aggregate per-quiz rows into the figures reported."""
    good = [r for r in rows if r["ok"]]
    n_q = sum(r["mcq"] + r["short"] for r in good)
    n_mcq = sum(r["mcq"] for r in good)
    ground_total = sum(r["verified"] + r["partial"] + r["unsupported"] for r in good)

    def spread(key):
        c = Counter(ch for r in good for ch in r[key])
        tot = sum(c.values()) or 1
        return {k: round(100 * c.get(k, 0) / tot, 1) for k in "0123"}

    bloom = {}
    for r in good:
        for lvl in filter(None, r["bloom_levels"].split("|")):
            bloom.setdefault(r["difficulty"], Counter())[lvl] += 1
    return {
        "quizzes": len(rows), "valid_rate": round(100 * len(good) / len(rows), 1) if rows else 0,
        "mean_seconds": round(sum(r["seconds"] for r in good) / len(good), 1) if good else None,
        "concept_tag_rate": round(100 * sum(r["with_concept"] for r in good) / n_q, 1) if n_q else None,
        "misconception_rate": round(100 * sum(r["mcq_with_misconceptions"] for r in good) / n_mcq, 1) if n_mcq else None,
        "hint_rate": round(100 * sum(r["with_hints"] for r in good) / n_q, 1) if n_q else None,
        "grounded_rate": round(100 * sum(r["verified"] for r in good) / ground_total, 1) if ground_total else None,
        "partial_rate": round(100 * sum(r["partial"] for r in good) / ground_total, 1) if ground_total else None,
        "unsupported_rate": round(100 * sum(r["unsupported"] for r in good) / ground_total, 1) if ground_total else None,
        "duplicate_questions": sum(r["duplicates"] for r in good),
        "answer_position_before": spread("answer_positions_before"), "answer_position_after": spread("answer_positions_after"),
        "bloom_by_difficulty": {d: dict(c) for d, c in bloom.items()},
    }


def write_outputs(rows: list[dict], summary: dict, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "results.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    pos = "\n".join(f"| {k} | {summary['answer_position_before'][k]}% | {summary['answer_position_after'][k]}% |" for k in "0123")
    md = f"""# Quiz generation evaluation

{summary['quizzes']} quizzes ({N_MCQ} multiple-choice and {N_SHORT} written questions each).

| Measure | Result |
|---|---|
| Valid quizzes | {summary['valid_rate']}% |
| Mean generation time | {summary['mean_seconds']} s |
| Questions tagged with a concept | {summary['concept_tag_rate']}% |
| MCQs with misconceptions for the wrong options | {summary['misconception_rate']}% |
| Questions with hints | {summary['hint_rate']}% |
| Source quote verified in the source text | {summary['grounded_rate']}% |
| Source quote partly supported | {summary['partial_rate']}% |
| Source quote not found | {summary['unsupported_rate']}% |
| Duplicate questions within a quiz | {summary['duplicate_questions']} |

Position of the correct answer (index 0 is the first option):

| Index | Before shuffling | After shuffling |
|---|---|---|
{pos}

Bloom levels by requested difficulty: {summary['bloom_by_difficulty']}
"""
    open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8").write(md)
    tex = ["\\begin{tabular}{lr}", "\\toprule", "Measure & Result \\\\", "\\midrule"]
    for label, key, unit in [("Valid quizzes", "valid_rate", "\\%"), ("Mean generation time", "mean_seconds", " s"),
                             ("Questions tagged with a concept", "concept_tag_rate", "\\%"),
                             ("MCQs with misconceptions", "misconception_rate", "\\%"), ("Questions with hints", "hint_rate", "\\%"),
                             ("Source quote verified", "grounded_rate", "\\%"), ("Source quote not found", "unsupported_rate", "\\%")]:
        tex.append(f"{label} & {summary[key]}{unit} \\\\")
    tex += ["\\bottomrule", "\\end{tabular}", ""]
    open(os.path.join(out_dir, "summary.tex"), "w", encoding="utf-8").write("\n".join(tex))


def _stub_runner():
    """Canned quizzes so the script can be tested without a model."""
    def run(topic, difficulty, **_):
        mk = lambda i: {"question": f"{topic} question {i}?", "options": ["a", "b", "c", "d"], "answer_index": 0, "concept": "Core",
                        "bloom": "Apply", "hints": ["h1", "h2"], "misconceptions": [None, "m1", "m2", "m3"], "source_quote": "x"}
        quiz = qe._validate({"concepts": [{"name": "Core", "prereqs": []}], "mcq": [mk(i) for i in range(N_MCQ)],
                             "short": [{"question": f"{topic} written {i}", "model_answer": "m", "concept": "Core", "bloom": "Understand"} for i in range(N_SHORT)]})
        for q in quiz["mcq"]:
            qe._shuffle_options(q)
        return {"quiz": quiz, "context": {"grounding": {"verified": 3, "partial": 1, "unsupported": 1}}}
    return run


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=int, default=1, help="repeat the topic list this many times")
    ap.add_argument("--pause", type=int, default=25, help="seconds between quizzes (Groq free tier is 8K tokens per minute)")
    ap.add_argument("--stub", action="store_true", help="use canned quizzes instead of calling a model")
    ap.add_argument("--out", default=os.path.join(ROOT, "report", "eval"))
    args = ap.parse_args()

    before: list[int] = []
    real_shuffle = qe._shuffle_options

    def spy(q, rng=None):
        before.append(q.get("answer_index"))
        return real_shuffle(q, rng)
    qe._shuffle_options = spy

    runner = _stub_runner() if args.stub else (lambda t, d, **k: qe.generate_topic_quiz(
        t, d, n_mcq=N_MCQ, n_short=N_SHORT, n_code=0, use_web=True, depth="standard"))
    rows = []
    for rep in range(args.runs):
        for topic, diff in TOPICS:
            before.clear()
            t0 = time.time()
            try:
                result = runner(topic, diff)
                rows.append(measure(topic, diff, result, time.time() - t0, list(before)))
                print(f"ok    {topic} ({diff}) {rows[-1]['seconds']}s", flush=True)
            except Exception as e:  # keep going: a failed quiz is a data point
                rows.append({k: "" for k in FIELDS} | {"topic": topic, "difficulty": diff, "ok": 0, "seconds": round(time.time() - t0, 1),
                                                       "mcq": 0, "short": 0, "verified": 0, "partial": 0, "unsupported": 0,
                                                       "duplicates": 0, "with_concept": 0, "mcq_with_misconceptions": 0, "with_hints": 0,
                                                       "answer_positions_before": "", "answer_positions_after": "", "error": str(e)[:160]})
                print(f"FAIL  {topic} ({diff}): {e}", flush=True)
            if not args.stub:
                time.sleep(args.pause)
    summary = summarise(rows)
    write_outputs(rows, summary, args.out)
    print(f"\nWrote {args.out}\n{summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
