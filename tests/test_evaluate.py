import importlib.util
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("evaluate", os.path.join(ROOT, "scripts", "evaluate.py"))
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)


def test_stub_run_measures_and_writes(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", ["evaluate.py", "--stub", "--out", str(tmp_path)])
    assert ev.main() == 0
    csv_text = (tmp_path / "results.csv").read_text(encoding="utf-8")
    assert csv_text.count("\n") == len(ev.TOPICS) + 1
    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "Valid quizzes | 100.0%" in md and "Source quote verified in the source text | 60.0%" in md
    assert r"\begin{tabular}" in (tmp_path / "summary.tex").read_text(encoding="utf-8")


def test_summarise_counts_failures_and_positions():
    ok = {"topic": "t", "difficulty": "Easy", "ok": 1, "seconds": 2.0, "mcq": 2, "short": 1, "concepts": 2, "with_concept": 3,
          "mcq_with_misconceptions": 2, "with_hints": 3, "bloom_levels": "Remember|Apply|Understand", "verified": 1, "partial": 1,
          "unsupported": 0, "duplicates": 1, "answer_positions_before": "00", "answer_positions_after": "13", "error": ""}
    bad = dict(ok, ok=0)
    s = ev.summarise([ok, bad])
    assert s["valid_rate"] == 50.0 and s["duplicate_questions"] == 1
    assert s["answer_position_before"]["0"] == 100.0 and s["answer_position_after"]["1"] == 50.0
    assert s["grounded_rate"] == 50.0 and s["bloom_by_difficulty"]["Easy"]["Apply"] == 1
