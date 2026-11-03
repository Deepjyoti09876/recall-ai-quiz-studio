"""Web research for topic quizzes.

Collects study material about any topic from the web so the quiz is grounded in
real sources instead of only the model's memory.

Sources (in order, all free):
  1. Tavily search API  - only if TAVILY_API_KEY is set in .env (best general web coverage)
  2. Wikipedia          - search + full plain-text extracts of the top articles
  3. DuckDuckGo         - instant-answer abstract (extra context / fallback)

If every source fails (offline, blocked), research() returns empty material and
the quiz engine falls back to the model's own knowledge.
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "RecallQuizStudio/2.0 (educational project; contact: local)"
TIMEOUT = 12


def _get_json(url: str, data: dict | None = None, headers: dict | None = None) -> dict:
    body = json.dumps(data).encode("utf-8") if data is not None else None
    h = {"User-Agent": UA, "Accept": "application/json"}
    if body is not None:
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    req = urllib.request.Request(url, data=body, headers=h)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _clean(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text or "")
    text = re.sub(r"==+\s*(See also|References|External links|Further reading|Notes)\s*==+.*",
                  "", text, flags=re.S | re.I)
    return text.strip()


# ---------- individual sources ----------
def _tavily(topic: str, max_results: int = 5) -> list[dict]:
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key:
        return []
    data = _get_json("https://api.tavily.com/search", {
        "api_key": key,
        "query": topic,
        "search_depth": "advanced",
        "max_results": max_results,
        "include_raw_content": False,
    })
    out = []
    for r in data.get("results", []):
        if r.get("content"):
            out.append({"title": r.get("title") or r.get("url"), "url": r.get("url"),
                        "site": urllib.parse.urlparse(r.get("url", "")).netloc,
                        "text": _clean(r["content"])})
    return out


def _wikipedia(topic: str, max_pages: int = 3, chars_per_page: int = 7000) -> list[dict]:
    q = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": topic,
                                "srlimit": max_pages, "format": "json", "utf8": 1})
    hits = _get_json(f"https://en.wikipedia.org/w/api.php?{q}").get("query", {}).get("search", [])
    titles = [h["title"] for h in hits][:max_pages]
    if not titles:
        return []
    q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "explaintext": 1,
                                "exsectionformat": "wiki", "titles": "|".join(titles),
                                "format": "json", "redirects": 1})
    pages = _get_json(f"https://en.wikipedia.org/w/api.php?{q}").get("query", {}).get("pages", {})
    by_title = {p.get("title"): p for p in pages.values()}
    out = []
    for t in titles:
        p = by_title.get(t)
        if not p or not p.get("extract"):
            continue
        out.append({"title": t,
                    "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(t.replace(" ", "_")),
                    "site": "wikipedia.org",
                    "text": _clean(p["extract"])[:chars_per_page]})
    return out


def _duckduckgo(topic: str) -> list[dict]:
    q = urllib.parse.urlencode({"q": topic, "format": "json", "no_html": 1, "skip_disambig": 1})
    d = _get_json(f"https://api.duckduckgo.com/?{q}")
    text = d.get("AbstractText") or ""
    related = [r.get("Text", "") for r in d.get("RelatedTopics", []) if isinstance(r, dict) and r.get("Text")]
    body = "\n".join([text] + related[:8]).strip()
    if len(body) < 60:
        return []
    return [{"title": d.get("Heading") or topic, "url": d.get("AbstractURL") or "https://duckduckgo.com/?q=" + urllib.parse.quote(topic),
             "site": d.get("AbstractSource") or "duckduckgo.com", "text": body}]


# ---------- public API ----------
def research(topic: str, depth: str = "standard") -> dict:
    """Return {"material": str, "sources": [{title, url, site}], "errors": [str]}.

    depth: "quick" (1 wiki page), "standard" (3), "deep" (5 + more text per page).
    """
    topic = (topic or "").strip()
    if not topic:
        return {"material": "", "sources": [], "errors": ["Empty topic"]}

    pages = {"quick": 1, "standard": 3, "deep": 5}.get(depth, 3)
    per_page = 9000 if depth == "deep" else 7000
    jobs = {
        "tavily": lambda: _tavily(topic, max_results=pages + 2),
        "wikipedia": lambda: _wikipedia(topic, max_pages=pages, chars_per_page=per_page),
        "duckduckgo": lambda: _duckduckgo(topic),
    }
    results, errors = {}, []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {name: pool.submit(fn) for name, fn in jobs.items()}
        for name, fut in futures.items():
            try:
                results[name] = fut.result()
            except Exception as e:  # network blocked, timeout, bad JSON ...
                results[name] = []
                errors.append(f"{name}: {e.__class__.__name__}")

    docs, seen = [], set()
    for name in ("tavily", "wikipedia", "duckduckgo"):
        for d in results.get(name, []):
            if d["url"] in seen:
                continue
            seen.add(d["url"])
            docs.append(d)

    material = "\n\n".join(f"### SOURCE {i + 1}: {d['title']} ({d['site']})\n{d['text']}"
                           for i, d in enumerate(docs))
    return {
        "material": material[:30_000],
        "sources": [{"title": d["title"], "url": d["url"], "site": d["site"]} for d in docs],
        "errors": errors,
    }
