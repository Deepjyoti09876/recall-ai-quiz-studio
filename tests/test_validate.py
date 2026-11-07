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
