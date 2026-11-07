import pytest

from recall import rag


@pytest.fixture(autouse=True)
def _bm25(monkeypatch):
    monkeypatch.setenv("RECALL_RAG", "bm25")
    rag._INDEX_CACHE.clear()


def _doc(n_sections=40):
    parts = []
    for i in range(n_sections):
        topic = "Quantum Decoherence" if i == 33 else f"Filler Topic {i}"
        body = " ".join(f"Sentence {j} about {topic.lower()} and unrelated ordinary material." for j in range(14))
        parts.append(f"## {topic}\n\n{body}")
    return "\n\n".join(parts)


def test_chunk_bounds_and_headings():
    ch = rag.chunk(_doc(), size=1000, overlap=150)
    assert ch and all(len(c["text"]) <= 1000 + 150 + 5 for c in ch)
    assert any(c["heading"] == "Quantum Decoherence" for c in ch)


def test_chunk_numbered_heading_and_tiny_input():
    ch = rag.chunk("2.1 Scheduling Basics\n\nThe scheduler picks the next process to run on the CPU core.")
    assert ch[0]["heading"].startswith("2.1")
    assert rag.chunk("") == []


def test_short_text_unchanged():
    out, meta = rag.select_context("short text", 500)
    assert out == "short text" and meta["retriever"] == "full"


def test_focus_retrieves_late_section_in_order_and_budget():
    text = _doc()
    assert text.index("Quantum Decoherence") > 35000 or len(text) > 30000
    out, meta = rag.select_context(text, 4000, {"concepts": ["Quantum Decoherence"]})
    assert len(out) <= 4000 and "Quantum Decoherence" in out
    assert meta["retriever"] == "bm25" and meta["chunks_used"] < meta["chunks_total"]


def test_index_cache_reused_across_focus(monkeypatch):
    calls = []
    real = rag.chunk
    monkeypatch.setattr(rag, "chunk", lambda *a, **k: calls.append(1) or real(*a, **k))
    text = _doc()
    rag.select_context(text, 4000, {"concepts": ["Filler Topic 3"]})
    rag.select_context(text, 4000, {"concepts": ["Quantum Decoherence"]})
    assert len(calls) == 1


def test_off_and_stride(monkeypatch):
    text = _doc()
    monkeypatch.setenv("RECALL_RAG", "off")
    out, meta = rag.select_context(text, 3000)
    assert out == text[:3000] and meta["retriever"] == "truncate"
    monkeypatch.setenv("RECALL_RAG", "bm25")
    monkeypatch.setattr(rag, "_bm25_available", lambda: False)
    rag._INDEX_CACHE.clear()
    out, meta = rag.select_context(text, 3000)
    assert meta["retriever"] == "stride" and 0 < len(out) <= 3000
