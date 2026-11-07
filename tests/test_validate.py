from recall import quiz_engine as q
from recall.server import app, _settings


def _mcq(**kw):
    d = {"question": "Q", "options": ["a", "b", "c", "d"], "answer_index": 1}
    d.update(kw)
    return d


def test_concepts_dedupe_selfref_default_general():
    v = q._validate({"concepts": ["Big O", "big o", {"name": "Sorting", "prereqs": ["Big O", "Sorting"]}],
                     "mcq": [_mcq(concept="sorting")], "short": [{"question": "x", "model_answer": "y"}]})
    names = [c["name"] for c in v["concepts"]]
    assert names.count("Big O") == 1 and "General" in names
    assert [c for c in v["concepts"] if c["name"] == "Sorting"][0]["prereqs"] == ["Big O"]
    assert v["mcq"][0]["concept"] == "Sorting"


def test_clean_name():
    assert q._clean_name("  \x00Hello   World.. ") == "Hello World"
    assert len(q._clean_name("x" * 200)) == 60


def test_misconceptions_and_answer_index():
    v = q._validate({"mcq": [_mcq(answer_index="1", misconceptions=["a", "b", "c", "d"]), _mcq(misconceptions="bad")]})
    assert v["mcq"][0]["answer_index"] == 1 and v["mcq"][0]["misconceptions"][1] is None
    assert v["mcq"][1]["misconceptions"] == [None] * 4


def test_concepts_only_is_not_a_quiz():
    v = q._validate({"concepts": ["A"]})
    assert not q._has_questions(v)


def test_budget_and_focus_prompt():
    assert q.context_budget(5, 2, 0, True) == 7000
    assert q.context_budget(20, 10, 5, True) == 2400
    assert q.context_budget(5, 2, 0, False) == 10000
    p = q.build_prompt("text", "Easy", 1, 0, 0, "Python", focus={"concepts": ["Graphs"], "vocab": ["Trees"]})
    assert "Graphs" in p and "Trees" in p


def test_settings_focus_caps():
    s = _settings({"focus_concepts": ["A", 5, "B" * 100] + ["x%d" % i for i in range(20)], "concept_vocab": "no"})
    assert len(s["focus"]["concepts"]) == 8 and len(s["focus"]["concepts"][1]) == 60 and s["focus"]["vocab"] == []
    assert _settings({})["focus"] is None


def test_endpoints():
    c = app.test_client()
    caps = c.get("/api/status").json["capabilities"]
    assert caps["rag"] and caps["learning"] and "embeddings" in caps
    assert "Disallow: /api/" in c.get("/robots.txt").text
    assert "<urlset" in c.get("/sitemap.xml").text
    assert c.get("/llms.txt").text.startswith("# Recall")
    assert c.get("/manifest.webmanifest").json["short_name"] == "Recall"


def test_grade_batch_parsing_and_fallback(monkeypatch):
    items = [{"answer": "a", "model_answer": "m", "key_points": ["k"]}, {"answer": "b", "model_answer": "m2"}]
    monkeypatch.setattr(q, "_grade_call", lambda *a, **k: {"grades": [
        {"score": "85", "hits": ["k"], "misses": [], "feedback": "good", "misconception": "ignored when passing"},
        {"score": 20, "hits": [], "misses": ["x"], "feedback": "weak", "misconception": "Confuses X with Y"}]})
    g = q.grade_short_batch(items)
    assert [x["score"] for x in g] == [85, 20] and g[0]["misconception"] is None and g[1]["misconception"] == "Confuses X with Y"
    monkeypatch.setattr(q, "_grade_call", lambda *a, **k: {"grades": [{"score": 1}]})  # wrong length
    assert [x["score"] for x in q.grade_short_batch(items)] == [0, 0]
    def boom(*a, **k):
        raise RuntimeError("down")
    monkeypatch.setattr(q, "_grade_call", boom)
    assert len(q.grade_short_batch(items)) == 2
    assert len(q.grade_short_batch(items * 5)) == q.MAX_BATCH


def test_grade_batch_endpoint(monkeypatch):
    import recall.server as srv
    monkeypatch.setattr(srv, "grade_short_batch", lambda items, engine="auto": [{"score": 90}] * len(items))
    c = app.test_client()
    assert c.post("/api/grade/batch", json={"items": []}).status_code == 400
    r = c.post("/api/grade/batch", json={"items": [{"answer": "x"}, {"answer": "  "}]})
    assert r.status_code == 200 and len(r.json["grades"]) == 1
