"""Core logic: builds the prompt, calls LLM (Groq Cloud or local Ollama), parses and validates quiz JSON."""
import json
import os
import re
import time
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_FALLBACK_MODEL = "llama-3.3-70b-versatile"
LOCAL_MODEL = os.getenv("LOCAL_MODEL", "llama3.2:3b")

DIFFICULTY_GUIDE = {
    "Easy": "Recall and definitions. Direct facts from the text. Obvious distractors. "
            "Coding: simple one-concept tasks (loops, conditionals, basic functions).",
    "Medium": "Understanding and application. Apply concepts to small scenarios. Plausible distractors. "
              "Coding: moderate logic, standard data structures, small algorithms.",
    "Hard": "Analysis and problem solving. Multi-step reasoning, edge cases, subtle distractors. "
            "Coding: optimisation, complexity analysis, tricky edge cases.",
}

SYSTEM = (
    "You are an expert university examiner for B.Tech Computer Science. "
    "Create quiz questions ONLY from the provided material. "
    "For each MCQ, ensure distractors are plausible and include a source_quote (exact short excerpt justifying the answer). "
    "Respond with a single valid JSON object and nothing else (no markdown fences)."
)

SCHEMA = """{
  "mcq": [{"question": str, "options": [str, str, str, str], "answer_index": 0-3, "explanation": str, "source_quote": str}],
  "short": [{"question": str, "model_answer": str, "key_points": [str]}],
  "coding": [{"question": str, "language": str, "starter_code": str, "solution": str,
              "test_cases": [{"input": str, "expected_output": str}], "explanation": str}]
}"""


def build_prompt(text, difficulty, n_mcq, n_short, n_code, language, max_chars=30_000):
    return f"""Generate a quiz from the material below.

Difficulty: {difficulty}. Guidance: {DIFFICULTY_GUIDE[difficulty]}
Counts: {n_mcq} MCQs, {n_short} short-answer questions, {n_code} coding questions.
Coding language: {language}. If the material has no programming content, base coding questions on its concepts.
MCQs need exactly 4 options and one correct answer. Return an empty list for any type with count 0.

JSON schema:
{SCHEMA}

MATERIAL:
\"\"\"
{text[:max_chars]}
\"\"\""""


def _parse(raw: str) -> dict:
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in response")
    return json.loads(raw[start:end + 1])


def _validate(data: dict) -> dict:
    mcq = [q for q in data.get("mcq", [])
           if len(q.get("options", [])) == 4 and q.get("answer_index") in (0, 1, 2, 3)]
    short = [q for q in data.get("short", []) if q.get("question") and q.get("model_answer")]
    coding = [q for q in data.get("coding", []) if q.get("question") and q.get("solution")]
    return {"mcq": mcq, "short": short, "coding": coding}


def _call_groq_llm(prompt: str, model: str = None, system: str = None) -> str:
    """Ultra-fast cloud generation via Groq API (2-3 seconds)."""
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured in .env")
    model = model or GROQ_MODEL
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system or SYSTEM},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "RecallQuiz/1.0"
        }
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


def _call_local_llm(prompt: str, model: str = None, system: str = None) -> str:
    """Generate quiz content with a local Ollama model."""
    import ollama
    model = model or LOCAL_MODEL
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system or SYSTEM},
                {"role": "user", "content": prompt},
            ],
            format="json",
            stream=False,
        )
        return response.message.content
    except Exception as e:
        message = (
            f"Ollama error: Ensure Ollama is running and '{model}' is downloaded. "
            f"Run: ollama pull {model}. Details: {e}"
        )
        raise RuntimeError(message) from e


def get_available_engines() -> dict[str, str]:
    """Returns available engines with status labels."""
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY", "")
    engines = {}
    if api_key and api_key.startswith("gsk_"):
        engines["groq"] = f"Groq Cloud ({GROQ_MODEL} · Fast)"
    engines["ollama"] = f"Ollama Local ({LOCAL_MODEL} · Offline)"
    return engines


TOPIC_SYSTEM = (
    "You are an expert university examiner and subject tutor. "
    "Create accurate, well-balanced quiz questions about the requested topic. "
    "When web research material is provided, base questions on it and quote it in source_quote; "
    "otherwise use well-established, uncontroversial knowledge and leave source_quote as a short "
    "factual justification. Never invent facts. "
    "Respond with a single valid JSON object and nothing else (no markdown fences)."
)


def build_topic_prompt(topic, material, difficulty, n_mcq, n_short, n_code, language, max_chars=30_000):
    if material and material.strip():
        ctx = (f"Web research material about the topic (from several sources):\n\"\"\"\n"
               f"{material[:max_chars]}\n\"\"\"")
    else:
        ctx = "No web material is available - use your own reliable knowledge of the topic."
    return f"""Generate a quiz on the topic: "{topic}"

Cover the most important sub-topics of "{topic}" (definitions, how it works, examples, applications,
common misconceptions). Spread questions across sub-topics instead of repeating one idea.
Difficulty: {difficulty}. Guidance: {DIFFICULTY_GUIDE[difficulty]}
Counts: {n_mcq} MCQs, {n_short} short-answer questions, {n_code} coding questions.
Coding language: {language}. If the topic is not about programming, base coding questions on a small
computation related to the topic. Coding test_cases use stdin input and exact stdout output.
MCQs need exactly 4 options and one correct answer. Return an empty list for any type with count 0.

JSON schema:
{SCHEMA}

{ctx}"""


def _use_groq(engine: str) -> bool:
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY", "")
    return (engine == "groq") or (engine == "auto" and bool(api_key and api_key.startswith("gsk_")))


def generate_topic_quiz(topic, difficulty="Medium", n_mcq=5, n_short=3, n_code=0,
                        language="Python", engine="auto", use_web=True, depth="standard"):
    """Create a quiz about any topic. Returns {"quiz": {...}, "sources": [...], "web_used": bool}."""
    topic = (topic or "").strip()
    if len(topic) < 2:
        raise ValueError("Please type a topic (for example: 'Dijkstra's algorithm').")
    if len(topic) > 300:
        raise ValueError("Topic is too long - keep it under 300 characters, or use 'From documents' for long text.")

    material, sources = "", []
    if use_web:
        from .research import research
        found = research(topic, depth=depth)
        material, sources = found["material"], found["sources"]

    use_groq = _use_groq(engine)
    max_chars = 9_000 if use_groq else 10_000
    prompt = build_topic_prompt(topic, material, difficulty, n_mcq, n_short, n_code, language, max_chars)
    quiz = _run_prompt(prompt, use_groq, system=TOPIC_SYSTEM)
    return {"quiz": quiz, "sources": sources, "web_used": bool(material)}


def _describe_groq_error(e: Exception) -> str:
    """Turn a Groq failure into one plain sentence."""
    code = getattr(e, "code", None)
    if code in (401, 403):
        return ("Groq refused the request (HTTP %s). Your network, VPN or WARP may be blocked by Groq, "
                "or the API key is invalid. Try another network, turn the VPN off, or check GROQ_API_KEY." % code)
    if code == 429:
        return "Groq rate limit reached. Wait a minute and try again."
    if code in (400, 404):
        return f"Groq rejected the model or request (HTTP {code}). Check GROQ_MODEL in .env."
    if isinstance(e, (urllib.error.URLError, TimeoutError, OSError)):
        return "Could not reach Groq. Check your internet connection."
    return f"Groq error: {e}"


_BAD_MODELS: set[str] = set()


_MODEL_CACHE: dict = {"t": 0.0, "ids": []}
_SKIP_WORDS = ("whisper", "orpheus", "guard", "safeguard", "tts", "embed", "distil-whisper")
_PREFERRED = ("openai/gpt-oss-120b", "qwen/", "openai/gpt-oss-20b", "llama-3.3", "llama-3.1")


def _groq_models() -> list[str]:
    """Return the list of Groq models that are currently available to this key."""
    now = time.time()
    if not _MODEL_CACHE["ids"] or now - _MODEL_CACHE["t"] > 600:
        try:
            key = os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY", "")
            req = urllib.request.Request("https://api.groq.com/openai/v1/models",
                                         headers={"Authorization": f"Bearer {key}", "User-Agent": "RecallQuiz/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                ids = [m["id"] for m in json.loads(r.read().decode("utf-8")).get("data", [])]
            ids = [i for i in ids if not any(w in i for w in _SKIP_WORDS)]
            if ids:
                _MODEL_CACHE.update(t=now, ids=ids)
        except Exception:
            pass
    rank = lambda i: next((n for n, p in enumerate(_PREFERRED) if i.startswith(p)), len(_PREFERRED))
    ordered = sorted(_MODEL_CACHE["ids"], key=lambda i: (rank(i), i))
    return [m for m in dict.fromkeys([GROQ_MODEL] + ordered) if m not in _BAD_MODELS]


def _groq_retry(prompt: str, model: str, system: str = None) -> str:
    """Call Groq, retrying brief network hiccups (dropped connection, timeout, 5xx)."""
    last = None
    for attempt in range(3):
        try:
            return _call_groq_llm(prompt, model=model, system=system)
        except urllib.error.HTTPError as e:
            if e.code < 500:
                raise
            last = e
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            last = e
        time.sleep(1.5 * (attempt + 1))
    raise last


def _run_prompt(prompt: str, use_groq: bool, system: str = None) -> dict:
    """Try Groq with a fallback to local Ollama and return the best valid quiz."""
    problems = []
    if use_groq:
        models = _groq_models()
        for round_no in range(4):
            limited, wait = False, 0
            for m in models:
                try:
                    validated = _validate(_parse(_groq_retry(prompt, m, system)))
                    if any(validated.values()):
                        return validated
                    problems.append("Groq returned no usable questions.")
                except Exception as e:
                    code = getattr(e, "code", None)
                    if code in (400, 404):
                        if code == 404:
                            _BAD_MODELS.add(m)
                        continue
                    if code == 429:
                        limited = True
                        try:
                            wait = max(wait, min(max(float(e.headers.get("retry-after", 12)), 12), 25))
                        except Exception:
                            wait = max(wait, 12)
                        continue
                    msg = _describe_groq_error(e)
                    if msg not in problems:
                        problems.append(msg)
                    if code in (401, 403):
                        limited = False
                        break
            if not limited:
                break
            if round_no < 3:
                time.sleep(wait or 12)
            else:
                problems.append("Groq rate limit reached on every model. Wait a minute and try again.")
    for attempt in range(2):
        try:
            validated = _validate(_parse(_call_local_llm(prompt, system=system)))
            if any(validated.values()):
                return validated
            problems.append("Ollama returned no usable questions.")
        except Exception as e:
            first = str(e).split(" Details:")[0]
            problems.append(first)
            if "Ensure Ollama is running" in first:
                break
    raise RuntimeError("Could not generate the quiz. " + " ".join(dict.fromkeys(problems)))


def generate_quiz(text, difficulty="Medium", n_mcq=5, n_short=3, n_code=2,
                  language="Python", engine="auto"):
    if not text or len(text.strip()) < 80:
        raise ValueError("Not enough text found in the uploaded material (minimum 80 characters).")

    api_key = os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY", "")
    use_groq = (engine == "groq") or (engine == "auto" and bool(api_key and api_key.startswith("gsk_")))

    max_chars = 9_000 if use_groq else 10_000
    prompt = build_prompt(text, difficulty, n_mcq, n_short, n_code, language, max_chars=max_chars)

    return _run_prompt(prompt, use_groq)


def grade_short_answer(user_answer: str, model_answer: str, key_points: list[str], engine="auto") -> dict:
    """Grade a short answer against model answer and key points."""
    key_points_text = "\n".join(f"- {kp}" for kp in key_points) if key_points else "None"
    prompt = f"""Compare the student's answer against the model answer and key points.

Model Answer:
{model_answer}

Key Points:
{key_points_text}

Student Answer:
{user_answer}

Evaluate the student's answer against the model answer and key points.
Return a valid JSON object with the following fields:
{{
  "score": 0-100,
  "hits": ["key points covered"],
  "misses": ["key points missed"],
  "feedback": "brief feedback string"
}}"""

    system_grading = (
        "You are an expert university examiner for B.Tech Computer Science. "
        "Respond with a single valid JSON object and nothing else (no markdown fences)."
    )

    api_key = os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY", "")
    use_groq = (engine == "groq") or (engine == "auto" and bool(api_key and api_key.startswith("gsk_")))

    try:
        if use_groq:
            url = "https://api.groq.com/openai/v1/chat/completions"
            payload = json.dumps({
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_grading},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2
            }).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "Recall/1.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return _parse(data["choices"][0]["message"]["content"])
        else:
            import ollama
            response = ollama.chat(
                model=LOCAL_MODEL,
                messages=[
                    {"role": "system", "content": system_grading},
                    {"role": "user", "content": prompt},
                ],
                format="json",
                stream=False,
            )
            return _parse(response.message.content)
    except Exception:
        return {
            "score": 0,
            "hits": [],
            "misses": key_points,
            "feedback": "Could not grade automatically. Compare with the model answer.",
        }


def to_markdown(quiz: dict, difficulty: str) -> str:
    out = [f"# Quiz ({difficulty})\n"]
    for i, q in enumerate(quiz.get("mcq", []), 1):
        out.append(f"**Q{i}. {q['question']}**")
        out += [f"- {chr(65 + j)}. {o}" for j, o in enumerate(q["options"])]
        quote = f" [Source: \"{q['source_quote']}\"]" if q.get("source_quote") else ""
        out.append(f"\nAnswer: {chr(65 + q['answer_index'])}. {q.get('explanation', '')}{quote}\n")
    for i, q in enumerate(quiz.get("short", []), 1):
        out.append(f"**Short {i}. {q['question']}**\n\nModel answer: {q['model_answer']}\n")
    for i, q in enumerate(quiz.get("coding", []), 1):
        out.append(f"**Coding {i}. {q['question']}**\n\n```{q.get('language', 'python').lower()}\n{q['solution']}\n```\n")
    return "\n".join(out)
