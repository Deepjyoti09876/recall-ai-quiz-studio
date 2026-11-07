"""Local, wait-free retrieval for long source material.

Instead of cutting the text at N characters, `select_context` picks the chunks that matter most:

  Tier A  dense embeddings  (fastembed, BAAI/bge-small-en-v1.5)  - used once the model is warm
  Tier B  BM25 lexical      (rank_bm25)                          - used while the model is warming up / missing
  Tier C  stride sampling   (no dependencies)                    - always works

Selection uses Maximal Marginal Relevance so the chosen chunks are relevant AND not repetitive.
A request never waits for the model download: if the embedding model is not ready, BM25 answers at once.

Env: RECALL_RAG = auto (default) | bm25 | off      FASTEMBED_CACHE_PATH = model cache folder
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import threading
from collections import OrderedDict

import numpy as np

MODEL_NAME = "BAAI/bge-small-en-v1.5"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
_CACHE_MAX = 8

_MODEL_READY = threading.Event()
_MODEL = None
_MODEL_ERROR: str | None = None
_WARM_STARTED = False
_WARM_LOCK = threading.Lock()
_INDEX_LOCK = threading.Lock()
_INDEX_CACHE: "OrderedDict[tuple, dict]" = OrderedDict()

_STOP = frozenset("the a an and or of to in on for with is are was were be been it this that as at by from "
                  "which what how why when who not no can will do does did has have had its into than then "
                  "also such these those their there they them you your we our".split())

_MD_HEAD = re.compile(r"^#{1,6}\s+(.+)$")
_NUM_HEAD = re.compile(r"^\d+(?:\.\d+){0,3}[.)]?\s+[A-Z][^\n]{2,70}$")


def _mode() -> str:
    m = (os.getenv("RECALL_RAG") or "auto").strip().lower()
    return m if m in ("auto", "bm25", "off") else "auto"


# ---------------------------------------------------------------- chunking

def _is_heading(line: str) -> str | None:
    s = line.strip()
    if not s or len(s) > 80:
        return None
    m = _MD_HEAD.match(s)
    if m:
        return m.group(1).strip()
    if _NUM_HEAD.match(s) and not s.endswith((".", ",", ";")):
        return s
    words = s.split()
    if len(words) <= 10 and not s.endswith((".", ",", ";", ":")) and (
            (s.isupper() and len(s) >= 4) or (s[0].isupper() and len(words) <= 6 and not re.search(r"[.!?]", s))):
        return s
    return None


def _split_long(par: str, size: int) -> list[str]:
    if len(par) <= size:
        return [par]
    out, cur = [], ""
    for sent in re.split(r"(?<=[.!?])\s+", par):
        while len(sent) > size:  # hard split on word boundary
            cut = sent.rfind(" ", 0, size)
            cut = cut if cut > size // 2 else size
            if cur:
                out.append(cur)
                cur = ""
            out.append(sent[:cut].strip())
            sent = sent[cut:].strip()
        if cur and len(cur) + len(sent) + 1 > size:
            out.append(cur)
            cur = sent
        else:
            cur = f"{cur} {sent}".strip()
    if cur:
        out.append(cur)
    return out


def chunk(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Split text into <= size char chunks (plus overlap), each tagged with its section heading."""
    text = re.sub(r"[ \t]+", " ", (text or "").replace("\r", ""))
    pieces: list[tuple[str, str]] = []  # (heading, paragraph)
    heading = ""
    for block in re.split(r"\n\s*\n", text):
        lines = [l for l in block.split("\n") if l.strip()]
        if not lines:
            continue
        body = []
        for l in lines:
            h = _is_heading(l) if len(lines) == 1 or not body else None
            if h and not body:
                heading = h
            else:
                body.append(l.strip())
        par = " ".join(body).strip()
        if par:
            for part in _split_long(par, size):
                pieces.append((heading, part))

    chunks: list[dict] = []
    cur, cur_head = "", ""
    for head, par in pieces:
        if cur and (head != cur_head or len(cur) + len(par) + 1 > size):
            chunks.append({"heading": cur_head, "text": cur})
            cur = ""
        if not cur:
            cur_head = head
        cur = f"{cur}\n{par}".strip() if cur else par
    if cur:
        chunks.append({"heading": cur_head, "text": cur})

    out = []
    for i, c in enumerate(chunks):
        body = c["text"]
        if i and overlap and chunks[i - 1]["heading"] == c["heading"]:
            tail = chunks[i - 1]["text"][-overlap:]
            sp = tail.find(" ")
            body = (tail[sp + 1:] if 0 <= sp < len(tail) - 1 else tail) + " " + body
        if len(body.strip()) >= 40 or len(chunks) == 1:
            out.append({"index": len(out), "heading": c["heading"], "text": body.strip()})
    return out


def headings(chunks: list[dict], limit: int = 12) -> list[str]:
    seen, out = set(), []
    for c in chunks:
        h = c["heading"]
        if h and h.lower() not in seen:
            seen.add(h.lower())
            out.append(h)
    return out[:limit]


# ---------------------------------------------------------------- embeddings (Tier A)

def embeddings_available() -> bool:
    """True if fastembed is installed (does not load the model)."""
    return importlib.util.find_spec("fastembed") is not None


def model_ready() -> bool:
    return _MODEL_READY.is_set()


def _load_model():
    global _MODEL, _MODEL_ERROR
    try:
        from fastembed import TextEmbedding
        cache = os.getenv("FASTEMBED_CACHE_PATH") or os.path.join(os.path.expanduser("~"), ".cache", "recall-fastembed")
        os.makedirs(cache, exist_ok=True)
        _MODEL = TextEmbedding(MODEL_NAME, cache_dir=cache)
        list(_MODEL.embed(["warmup"]))
        _MODEL_READY.set()
    except Exception as e:  # missing package, offline first run, corrupt cache...
        _MODEL_ERROR = str(e)


def warmup() -> None:
    """Load the embedding model in a background thread. Never blocks, safe to call repeatedly."""
    global _WARM_STARTED
    if _mode() != "auto" or not embeddings_available():
        return
    with _WARM_LOCK:
        if _WARM_STARTED:
            return
        _WARM_STARTED = True
    threading.Thread(target=_load_model, name="rag-warmup", daemon=True).start()


def _normalize(m: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.maximum(n, 1e-12)


def _embed_passages(texts: list[str]) -> np.ndarray:
    return _normalize(np.array(list(_MODEL.passage_embed(texts)), dtype=np.float32))


def _embed_queries(texts: list[str]) -> np.ndarray:
    return _normalize(np.array(list(_MODEL.query_embed(texts)), dtype=np.float32))


# ---------------------------------------------------------------- BM25 (Tier B)

def _tokens(s: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]{2,}", s.lower()) if t not in _STOP]


def _bm25_available() -> bool:
    return importlib.util.find_spec("rank_bm25") is not None


# ---------------------------------------------------------------- index + cache

def _backend() -> str:
    mode = _mode()
    if mode == "off":
        return "stride"
    if mode == "auto" and _MODEL_READY.is_set() and _MODEL is not None:
        return "fastembed"
    if _bm25_available():
        return "bm25"
    return "stride"


def _get_index(text: str, backend: str) -> dict:
    key = (hashlib.sha1(text.encode("utf-8")).hexdigest(), CHUNK_SIZE, CHUNK_OVERLAP, backend)
    with _INDEX_LOCK:
        hit = _INDEX_CACHE.get(key)
        if hit:
            _INDEX_CACHE.move_to_end(key)
            return hit
    chunks = chunk(text)
    idx: dict = {"chunks": chunks, "backend": backend}
    if backend == "fastembed" and chunks:
        idx["vecs"] = _embed_passages([c["text"] for c in chunks])
    elif backend == "bm25" and chunks:
        from rank_bm25 import BM25Okapi
        toks = [_tokens(c["heading"] + " " + c["text"]) or ["_"] for c in chunks]
        idx["tokens"] = toks
        idx["sets"] = [set(t) for t in toks]
        idx["bm25"] = BM25Okapi(toks)
    with _INDEX_LOCK:
        _INDEX_CACHE[key] = idx
        while len(_INDEX_CACHE) > _CACHE_MAX:
            _INDEX_CACHE.popitem(last=False)
    return idx


def _minmax(a: np.ndarray) -> np.ndarray:
    if a.size == 0:
        return a
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / (hi - lo) if hi - lo > 1e-12 else np.zeros_like(a)


def _relevance_and_sim(idx: dict, queries: list[tuple[str, float]]):
    """Return (relevance[n], sim(i, j) callable) for the active backend."""
    chunks = idx["chunks"]
    n = len(chunks)
    backend = idx["backend"]
    if backend == "fastembed":
        vecs = idx["vecs"]
        rel = np.zeros(n, dtype=np.float32)
        qv = _embed_queries([q for q, _ in queries])
        for (q, w), v in zip(queries, qv):
            rel = np.maximum(rel, w * _minmax(vecs @ v))
        return rel, lambda i, j: float(vecs[i] @ vecs[j])
    if backend == "bm25":
        rel = np.zeros(n, dtype=np.float32)
        sets = idx["sets"]
        for q, w in queries:
            qt = _tokens(q)
            if qt:
                rel = np.maximum(rel, w * _minmax(np.array(idx["bm25"].get_scores(qt), dtype=np.float32)))

        def jac(i, j):
            a, b = sets[i], sets[j]
            return len(a & b) / max(1, len(a | b))
        return rel, jac
    return None, None


# ---------------------------------------------------------------- selection

def _fmt(c: dict) -> str:
    return f"[§ {c['heading']}]\n{c['text']}" if c["heading"] else c["text"]


def select_context(text: str, budget: int, focus: dict | None = None) -> tuple[str, dict]:
    """Choose the best <= budget characters of `text`. Returns (context, meta)."""
    text = text or ""
    meta = {"retriever": "full", "chunks_total": 1, "chunks_used": 1, "chars_in": len(text), "chars_out": len(text)}
    if len(text) <= budget:
        return text, meta
    if _mode() == "off":
        meta.update(retriever="truncate", chars_out=budget)
        return text[:budget], meta

    backend = _backend()
    idx = _get_index(text, backend)
    chunks = idx["chunks"]
    n = len(chunks)
    if n == 0:
        meta.update(retriever="truncate", chars_out=budget)
        return text[:budget], meta

    queries: list[tuple[str, float]] = []
    focus = focus or {}
    fq = " ".join((focus.get("concepts") or []) + (focus.get("notes") or [])).strip()
    if fq:
        queries.append((fq, 1.0))
    hs = headings(chunks)
    queries.extend((h, 0.8) for h in hs)

    rel, sim = (None, None)
    if backend != "stride":
        try:
            rel, sim = _relevance_and_sim(idx, queries or [(text[:400], 0.6)])
            if backend == "fastembed":  # document centroid
                cent = _normalize(idx["vecs"].mean(axis=0, keepdims=True))[0]
                rel = np.maximum(rel, 0.6 * _minmax(idx["vecs"] @ cent))
        except Exception:
            rel = None

    selected: list[int] = []
    used = 0
    if rel is None:  # Tier C: evenly spaced chunks
        step = max(1, n // max(1, budget // CHUNK_SIZE))
        for i in range(0, n, step):
            cost = len(_fmt(chunks[i])) + 3
            if used + cost > budget:
                break
            selected.append(i)
            used += cost
        backend = "stride"
    else:
        lam = 0.75 if fq else 0.60
        rem = set(range(n))
        if not fq and 0 in rem:  # keep the introduction when nothing specific is asked for
            cost = len(_fmt(chunks[0])) + 3
            if cost <= budget:
                selected.append(0)
                used += cost
                rem.discard(0)
        while rem:
            best, best_s = None, -1e9
            for i in rem:
                red = max((sim(i, j) for j in selected), default=0.0)
                s = lam * float(rel[i]) - (1 - lam) * red
                if s > best_s:
                    best, best_s = i, s
            cost = len(_fmt(chunks[best])) + 3
            rem.discard(best)
            if used + cost > budget:
                if used > budget * 0.85:
                    break
                continue
            selected.append(best)
            used += cost

    selected.sort()
    out = "\n…\n".join(_fmt(chunks[i]) for i in selected)
    meta = {"retriever": backend, "chunks_total": n, "chunks_used": len(selected),
            "chars_in": len(text), "chars_out": len(out)}
    return out, meta
