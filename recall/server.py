"""Recall - AI Quiz Studio web server.

Run:   python -m recall.server          ->  open http://localhost:8000

Serves the website in /static and a small JSON API:
  GET  /api/status           engines + capabilities
  POST /api/quiz/topic       quiz about any topic (researched on the web)
  POST /api/quiz/document    quiz from uploaded files and/or pasted text
  POST /api/grade            AI grading of a short answer
  POST /api/run              run code against test cases (Python sandbox)
  POST /api/export/markdown  quiz -> Markdown text
"""
from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

load_dotenv()

from .file_loader import extract_text  # noqa: E402
from .quiz_engine import (generate_quiz, generate_topic_quiz, get_available_engines,  # noqa: E402
                         grade_short_answer, to_markdown)
from .sandbox import run_tests  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")

app = Flask(__name__, static_folder=STATIC, static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024  # 40 MB upload limit

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
            depth=data.get("depth", "standard"))
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
        quiz = generate_quiz(text, s["difficulty"], s["n_mcq"], s["n_short"], s["n_code"],
                             s["language"], engine=s["engine"])
        return jsonify({"quiz": quiz, "files": names, "chars": len(text)})
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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"\n  Recall is running ->  http://localhost:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=os.getenv("FLASK_DEBUG") == "1", threaded=True)
