"""Recall - AI Quiz Studio web server.

Run:   python -m recall.server          ->  open http://localhost:8000

Serves the website in /static and a small JSON API:
  GET  /api/status           engines + capabilities
  POST /api/quiz/topic       quiz about any topic (researched on the web)
  POST /api/quiz/document    quiz from uploaded files and/or pasted text
  POST /api/grade            AI grading of a short answer
  POST /api/grade/batch      grade up to 6 written answers with one model call
  POST /api/run              run code against test cases (Python sandbox)
  POST /api/export/markdown  quiz -> Markdown text
  GET  /robots.txt /sitemap.xml /llms.txt /manifest.webmanifest   crawler + install metadata

Topic/document endpoints also accept optional adaptive hints in the settings:
  focus_concepts, focus_notes, concept_vocab   (lists of short strings)
"""
from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory

load_dotenv()

from . import rag
from .file_loader import extract_text
from .quiz_engine import (
    _clean_name,
    generate_quiz,
    generate_topic_quiz,
    get_available_engines,
    grade_short_answer,
    grade_short_batch,
    to_markdown,
)
from .sandbox import run_tests

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")

app = Flask(__name__, static_folder=STATIC, static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024

ALLOWED_EXT = {"pdf", "docx", "pptx", "txt", "md"}
DIFFICULTIES = {"Easy", "Medium", "Hard"}
LANGUAGES = {"Python", "Java", "C", "C++", "JavaScript"}


def _settings(src: dict) -> dict:
    """Read and clamp quiz settings coming from the browser."""
    def num(key, default, lo, hi):
        try:
            return max(lo, min(hi, int(src.get(key, default))))
        except (TypeError, ValueError):
            return default
    s = {
        "difficulty": src.get("difficulty") if src.get("difficulty") in DIFFICULTIES else "Medium",
        "n_mcq": num("n_mcq", 5, 0, 20),
        "n_short": num("n_short", 2, 0, 10),
        "n_code": num("n_code", 0, 0, 5),
        "language": src.get("language") if src.get("language") in LANGUAGES else "Python",
        "engine": src.get("engine") or "auto",
    }
    def names(key, max_items, limit):
        raw = src.get(key)
        if not isinstance(raw, list):
            return []
        out = []
        for x in raw:
            if isinstance(x, str):
                n = _clean_name(x, limit)
                if n and n not in out:
                    out.append(n)
            if len(out) >= max_items:
                break
        return out
    focus = {"concepts": names("focus_concepts", 8, 60),
             "notes": names("focus_notes", 3, 160),
             "vocab": names("concept_vocab", 40, 60)}
    s["focus"] = focus if any(focus.values()) else None
    if s["n_mcq"] + s["n_short"] + s["n_code"] == 0:
        raise ValueError("Choose at least one question.")
    return s


def _error(msg, code=400):
    return jsonify({"error": str(msg)}), code


@app.errorhandler(413)
def too_large(_):
    return _error("Files are too large (40 MB max in total).", 413)


@app.get("/")
def index():
    return send_from_directory(STATIC, "index.html")


@app.get("/api/status")
def status():
    engines = get_available_engines()
    return jsonify({
        "engines": [{"id": k, "label": v} for k, v in engines.items()],
        "capabilities": {
            "web_research": True,
            "tavily": bool(os.getenv("TAVILY_API_KEY")),
            "documents": True,
            "code_runner": True,
            "ai_grading": True,
            "rag": True,
            "embeddings": rag.embeddings_available(),
            "embeddings_ready": rag.model_ready(),
            "learning": True,
        },
    })


@app.post("/api/quiz/topic")
def quiz_topic():
    data = request.get_json(silent=True) or {}
    try:
        s = _settings(data)
        result = generate_topic_quiz(
            data.get("topic", ""), s["difficulty"], s["n_mcq"], s["n_short"], s["n_code"],
            s["language"], engine=s["engine"], use_web=bool(data.get("use_web", True)),
            depth=data.get("depth", "standard"), focus=s["focus"])
        return jsonify(result)
    except ValueError as e:
        return _error(e)
    except Exception as e:
        return _error(e, 502)


@app.post("/api/quiz/document")
def quiz_document():
    try:
        s = _settings(json.loads(request.form.get("settings", "{}")))
        parts, names = [request.form.get("text", "")], []
        for f in request.files.getlist("files"):
            ext = f.filename.lower().rsplit(".", 1)[-1] if "." in f.filename else ""
            if ext not in ALLOWED_EXT:
                return _error(f"Unsupported file type: {f.filename}. Use PDF, DOCX, PPTX, TXT or MD.")
            parts.append(extract_text(f.filename, f.read()))
            names.append(f.filename)
        text = "\n".join(p for p in parts if p)
        ctx = {}
        quiz = generate_quiz(text, s["difficulty"], s["n_mcq"], s["n_short"], s["n_code"],
                             s["language"], engine=s["engine"], focus=s["focus"], meta=ctx)
        return jsonify({"quiz": quiz, "files": names, "chars": len(text), "context": ctx})
    except ValueError as e:
        return _error(e)
    except Exception as e:
        return _error(e, 502)


@app.post("/api/grade")
def grade():
    d = request.get_json(silent=True) or {}
    if not str(d.get("answer", "")).strip():
        return _error("Write an answer first.")
    return jsonify(grade_short_answer(d["answer"], d.get("model_answer", ""),
                                      d.get("key_points", []), engine=d.get("engine", "auto")))


@app.post("/api/grade/batch")
def grade_batch():
    d = request.get_json(silent=True) or {}
    items = [i for i in (d.get("items") or []) if isinstance(i, dict) and str(i.get("answer", "")).strip()]
    if not items:
        return _error("No written answers to grade.")
    return jsonify({"grades": grade_short_batch(items, engine=d.get("engine", "auto"))})


@app.post("/api/run")
def run():
    d = request.get_json(silent=True) or {}
    code = d.get("code", "")
    if not code.strip():
        return _error("Write some code first.")
    return jsonify(run_tests(code, d.get("test_cases", []), (d.get("language") or "python").lower()))


@app.post("/api/export/markdown")
def export_md():
    d = request.get_json(silent=True) or {}
    return jsonify({"markdown": to_markdown(d.get("quiz", {}), d.get("difficulty", "Medium"))})


SITE_NAME = "Recall - Adaptive AI Quiz Studio"

LLMS_TXT = """# Recall - Adaptive AI Quiz Studio

> Recall turns a topic or uploaded documents (PDF, DOCX, PPTX, TXT, MD) into quizzes with multiple-choice,
> short-answer and coding questions, then adapts to the learner using client-side learning models.

## Features
- Adaptive practice: Bayesian Knowledge Tracing keeps a mastery estimate per concept.
- Spaced repetition: SM-2 schedules reviews of questions the learner missed or guessed.
- Confidence calibration: compares how sure a learner felt with whether they were right.
- Knowledge graph: concepts and their prerequisites, coloured by mastery.
- Mistake analysis: every wrong option carries the misconception that makes it tempting.
- Local retrieval: long documents are searched with local embeddings or BM25, not blindly truncated.

## Privacy and architecture
- The server is stateless. Mastery, schedules and history stay in the browser (localStorage).
- Quiz text is generated by one LLM request; all learning maths runs in the browser.

## API
- GET /api/status
- POST /api/quiz/topic, POST /api/quiz/document, POST /api/grade, POST /api/run
"""


def _origin() -> str:
    return request.host_url.rstrip("/")


@app.get("/robots.txt")
def robots():
    body = "User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: " + _origin() + "/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@app.get("/sitemap.xml")
def sitemap():
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           '  <url><loc>' + _origin() + '/</loc></url>\n</urlset>\n')
    return Response(xml, mimetype="application/xml")


@app.get("/llms.txt")
def llms():
    return Response(LLMS_TXT, mimetype="text/plain")


@app.get("/manifest.webmanifest")
def manifest():
    return jsonify({"name": SITE_NAME, "short_name": "Recall", "start_url": "/", "display": "standalone",
                    "background_color": "#0f172a", "theme_color": "#0f172a",
                    "description": "Adaptive AI quizzes from topics and documents."}
                   ), 200, {"Content-Type": "application/manifest+json"}


@app.after_request
def _headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    if request.path.startswith("/static/") and not app.debug:
        resp.headers["Cache-Control"] = "public, max-age=0, must-revalidate"  # ETag revalidation: never serve a stale script next to new HTML
    return resp


if __name__ == "__main__":
    rag.warmup()
    port = int(os.getenv("PORT", 8000))
    print(f"\n  Recall is running ->  http://localhost:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=os.getenv("FLASK_DEBUG") == "1", threaded=True)
