"""Recall - AI quiz studio.  Run:  streamlit run app.py
Flow: setup -> quiz -> results -> review.  Session keys: stage, qs, answers, i, mode, quiz_id.
Features: Practice/Exam modes, code sandbox, AI-graded short answers, retry mistakes loop."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
from html import escape as esc
import streamlit as st
from recall.file_loader import extract_text
from recall.quiz_engine import generate_quiz, to_markdown, get_available_engines
from theme import inject_css, icon

try:
    from recall.quiz_engine import grade_short_answer
except ImportError:
    grade_short_answer = None

try:
    from recall.sandbox import run_tests
except ImportError:
    run_tests = None

st.set_page_config(page_title="Recall · AI Quiz Studio", layout="wide", initial_sidebar_state="collapsed")
inject_css()
S = st.session_state
S.setdefault("stage", "setup")
S.setdefault("quiz_id", 0)
TYPES = {"mcq": "Multiple choice", "short": "Short answer", "coding": "Coding"}


def md(html: str):
    st.markdown(html, unsafe_allow_html=True)


# ---------- logic ----------
def start_quiz(quiz, difficulty, mode, timer_minutes=None, items_override=None):
    if items_override is not None:
        items = items_override
    else:
        items = [{**q, "type": t} for t in ("mcq", "short", "coding") for q in quiz[t]]
    S.quiz_id += 1  # new widget keys => no stale answers from a previous quiz
    S.update(quiz=quiz, qs=items, difficulty=difficulty, mode=mode, i=0, answers={},
             started=time.time(), finished=None, only_wrong=False, stage="quiz",
             flagged=set(), timer_minutes=timer_minutes,
             short_grades={}, code_results={}, retry_round=S.get("retry_round", 0))


def correct_text(q):
    return q["options"][q["answer_index"]]


def status(i, q):
    if q["type"] != "mcq":
        return "open" if str(S.answers.get(i, "")).strip() else "skipped"
    a = S.answers.get(i)
    return "skipped" if a is None else ("right" if a == correct_text(q) else "wrong")


def tally():
    st_ = [status(i, q) for i, q in enumerate(S.qs) if q["type"] == "mcq"]
    return st_.count("right"), len(st_)


def go(stage):
    S.stage = stage
    st.rerun()


def time_remaining():
    """Returns seconds remaining for exam timer, or None if no timer."""
    if S.mode != "Exam" or not S.get("timer_minutes"):
        return None
    elapsed = time.time() - S.started
    remaining = (S.timer_minutes * 60) - elapsed
    return max(0, remaining)


# ---------- screens ----------
def screen_setup():
    engines = get_available_engines()
    engine_names = list(engines.keys())

    md('<div class="brand"><span class="mark"></span>Recall</div>'
       '<p class="eyebrow">Your personal study studio</p>'
       '<h1 class="display">Turn what you’re learning into what you remember.</h1>'
       '<p class="lede">Add your study material, choose how you want to be challenged, and build a focused quiz in seconds.</p>')

    left, right = st.columns([1.12, .88], gap="large")
    with left:
        with st.container(border=True):
            md('<p class="eyebrow">01 · Study material</p><h3 style="font-family:Manrope,sans-serif;margin:.1rem 0 .4rem">Start with your notes</h3>')
            files = st.file_uploader("Upload files", type=["pdf", "docx", "pptx", "txt", "md"],
                                     accept_multiple_files=True, help="PDF, Word, PowerPoint, text, or Markdown")
            st.caption("Or paste a passage, class notes, or a topic outline")
            pasted = st.text_area("Notes or source text", height=170,
                                  placeholder="Paste your study material here… The more context you add, the more relevant your questions will be.",
                                  label_visibility="collapsed")
            if files:
                st.caption(f"{len(files)} file{'s' if len(files) != 1 else ''} ready · " + " · ".join(f.name for f in files[:3]))
    with right:
        with st.container(border=True):
            md('<p class="eyebrow">02 · Quiz design</p><h3 style="font-family:Manrope,sans-serif;margin:.1rem 0 .4rem">Make it yours</h3>')
            md('<div class="label">Difficulty</div>')
            difficulty = st.segmented_control("Difficulty", ["Easy", "Medium", "Hard"], default="Medium",
                                              label_visibility="collapsed") or "Medium"
            md('<div class="label">Study mode</div>')
            mode = st.segmented_control("Mode", ["Practice", "Exam"], default="Practice",
                                        label_visibility="collapsed") or "Practice"
            st.caption("Instant coaching" if mode == "Practice" else "Timed challenge · feedback at the end")
            if mode == "Exam":
                timer_minutes = st.select_slider("Exam duration", options=[10, 15, 20, 30, 45, 60, 90],
                                                   value=30, format_func=lambda x: f"{x} min")
            else:
                timer_minutes = None
            md('<div class="label">Question mix</div>')
            c1, c2, c3 = st.columns(3)
            n_mcq = c1.slider("Choice", 0, 15, 5)
            n_short = c2.slider("Written", 0, 10, 3)
            n_code = c3.slider("Code", 0, 5, 2)
            language = st.selectbox("Coding language", ["Python", "Java", "C", "C++", "JavaScript"])
            selected_engine = st.selectbox("AI engine", options=engine_names,
                                           format_func=lambda k: engines[k])

    md('<div style="height:.5rem"></div>')
    if st.button("Build my quiz", type="primary", use_container_width=True, icon=":material/arrow_forward:"):
        if n_mcq + n_short + n_code == 0:
            st.error("Choose at least one question.")
            return
        try:
            text = pasted + "\n" + "\n".join(extract_text(f.name, f.getvalue()) for f in files)
            engine_label = engines.get(selected_engine, selected_engine)
            with st.spinner(f"Generating questions with {engine_label}…"):
                quiz = generate_quiz(text, difficulty, n_mcq, n_short, n_code, language, engine=selected_engine)
            if not any(quiz.values()):
                st.error("The model returned no usable questions. Try again or add more material.")
                return
            S.engine = selected_engine
            S.retry_round = 0
            start_quiz(quiz, difficulty, mode, timer_minutes)
            st.rerun()
        except Exception as e:
            st.error(str(e))


def _render_exam_timer():
    """Render the exam timer and auto-submit if time is up."""
    remaining = time_remaining()
    if remaining is None:
        return
    mins, secs = divmod(int(remaining), 60)
    urgent = remaining < 60
    md(f'<div class="exam-timer {"urgent" if urgent else ""}">'
       f'<span class="timer-label">TIME</span> {mins:02d}:{secs:02d}</div>')
    if remaining <= 0:
        S.finished = time.time()
        go("results")


def _render_question_grid():
    """Render the clickable question navigation grid for exam mode."""
    n = len(S.qs)
    cells = []
    for j in range(n):
        s = status(j, S.qs[j])
        flagged = j in S.get("flagged", set())
        cls = "grid-cell"
        if j == S.i:
            cls += " current"
        elif s in ("right", "wrong"):
            cls += " answered"
        elif s == "open":
            cls += " answered"
        if flagged:
            cls += " flagged"
        cells.append(f'<span class="{cls}">{j + 1}</span>')
    md(f'<div class="q-grid">{"".join(cells)}</div>')

    # Navigation via selectbox (since HTML clicks can't set session state)
    cols = st.columns([3, 1])
    with cols[0]:
        jump = st.selectbox("Jump to question", range(1, n + 1), index=S.i,
                            label_visibility="collapsed", key=f"jump_{S.quiz_id}")
        if jump - 1 != S.i:
            S.i = jump - 1
            st.rerun()
    with cols[1]:
        flagged = S.i in S.get("flagged", set())
        flag_label = "Flagged" if flagged else "Flag for review"
        if st.button(flag_label, use_container_width=True, key=f"flag_{S.quiz_id}_{S.i}"):
            if flagged:
                S.flagged.discard(S.i)
            else:
                S.flagged.add(S.i)
            st.rerun()


def screen_quiz():
    items, i = S.qs, S.i
    n, q = len(items), items[S.i]

    # Exam mode: timer + question grid
    if S.mode == "Exam":
        _render_exam_timer()
        _render_question_grid()

    # Progress segments (both modes)
    segs = "".join(f'<span class="{"on" if j < i else "cur" if j == i else ""}"></span>' for j in range(n))
    md(f'<div class="seg" role="progressbar" aria-valuemin="1" aria-valuemax="{n}" aria-valuenow="{i + 1}">{segs}</div>'
       f'<p class="eyebrow">Question {i + 1} of {n} · {TYPES[q["type"]]} · {S.difficulty}</p>'
       f'<div class="qtext q-card">{esc(q["question"])}</div>')
    key = f"w_{S.quiz_id}_{i}"

    def save():
        S.answers[i] = S[key]

    if q["type"] == "mcq":
        cur = S.answers.get(i)
        st.radio("Answer", q["options"], index=q["options"].index(cur) if cur in q["options"] else None,
                 key=key, on_change=save, label_visibility="collapsed")
        if S.mode == "Practice" and S.answers.get(i) is not None:
            ok = S.answers[i] == correct_text(q)
            feedback_html = f'<div class="fb {"ok" if ok else "bad"}"><b>{"Correct" if ok else "Incorrect"}</b> '
            feedback_html += f'{"" if ok else "Answer: " + esc(correct_text(q)) + ". "}{esc(q.get("explanation", ""))}'
            # Show source quote if available
            if q.get("source_quote"):
                feedback_html += f'<div class="source-quote"><span class="k">Reference:</span> {esc(q["source_quote"])}</div>'
            feedback_html += '</div>'
            md(feedback_html)

    elif q["type"] == "short":
        default = S.answers.get(i, "")
        st.text_area("Your answer", value=default, key=key, on_change=save, height=130,
                     label_visibility="collapsed", placeholder="Write your answer…")
        S.answers.setdefault(i, default) if default else None

        # AI grading in practice mode
        if S.mode == "Practice" and grade_short_answer and str(S.answers.get(i, "")).strip():
            grade_key = f"grade_{S.quiz_id}_{i}"
            if st.button("Check answer", icon=":material/grading:", key=f"check_{S.quiz_id}_{i}",
                         use_container_width=True):
                with st.spinner("AI is grading your answer…"):
                    try:
                        grade = grade_short_answer(
                            S.answers[i],
                            q["model_answer"],
                            q.get("key_points", []),
                            engine=S.get("engine", "auto")
                        )
                        S.short_grades[i] = grade
                    except Exception:
                        S.short_grades[i] = {"score": 0, "hits": [], "misses": q.get("key_points", []),
                                             "feedback": "Grading failed. Compare with the model answer."}
                st.rerun()

            if i in S.get("short_grades", {}):
                grade = S.short_grades[i]
                score = grade.get("score", 0)
                ok = score >= 70
                md(f'<div class="fb {"ok" if ok else "bad"}">'
                   f'<b>Score: {score}%</b><br>{esc(grade.get("feedback", ""))}'
                   f'</div>')
                if grade.get("hits"):
                    md('<div class="grade-details">'
                       '<span class="k">Key points covered</span><br>'
                       + "".join(f'<span class="grade-hit"><span class="bullet">+</span> {esc(h)}</span><br>' for h in grade["hits"])
                       + '</div>')
                if grade.get("misses"):
                    md('<div class="grade-details">'
                       '<span class="k">Key points missed</span><br>'
                       + "".join(f'<span class="grade-miss"><span class="bullet">-</span> {esc(m)}</span><br>' for m in grade["misses"])
                       + '</div>')

    else:  # coding
        default = S.answers.get(i, q.get("starter_code", ""))
        st.text_area("Your code", value=default, key=key, on_change=save,
                     height=240, label_visibility="collapsed", placeholder="Write your code…")
        S.answers.setdefault(i, default) if default else None

        # Code sandbox — run tests
        if run_tests and q.get("test_cases"):
            if st.button("Run Tests", type="primary", use_container_width=True,
                         key=f"run_{S.quiz_id}_{i}"):
                user_code = S.answers.get(i, "")
                if not user_code.strip():
                    st.warning("Write some code first.")
                else:
                    with st.spinner("Running tests…"):
                        try:
                            result = run_tests(user_code, q["test_cases"],
                                               q.get("language", "python").lower())
                            S.code_results[i] = result
                        except Exception as e:
                            S.code_results[i] = {"passed": 0, "failed": len(q["test_cases"]),
                                                 "total": len(q["test_cases"]),
                                                 "results": [], "error": str(e)}
                    st.rerun()

            if i in S.get("code_results", {}):
                result = S.code_results[i]
                p, t = result["passed"], result["total"]
                ok = p == t
                md(f'<div class="fb {"ok" if ok else "bad"}">'
                   f'<b>{"All tests passed" if ok else f"{p}/{t} tests passed"}</b></div>')
                for j, tr in enumerate(result.get("results", [])):
                    status_text = "PASSED" if tr["passed"] else "FAILED"
                    with st.expander(f"Test {j + 1}: {status_text}", expanded=not tr["passed"]):
                        st.code(f"Input:    {tr['input']}\nExpected: {tr['expected']}\nActual:   {tr['actual']}",
                                language="text")
                        if tr.get("error"):
                            st.error(tr["error"])
        elif not run_tests:
            st.caption("Code execution not available. Install sandbox.py to enable test running.")

    md("<div style='height:1.2rem'></div>")
    last = i == n - 1
    c1, c2 = st.columns(2)
    if c1.button("Previous", icon=":material/arrow_back:", disabled=i == 0, use_container_width=True):
        S.i -= 1
        st.rerun()

    if S.mode == "Exam" and last:
        # Exam: show submit button with confirmation
        if c2.button("Submit exam", type="primary", use_container_width=True, icon=":material/check:"):
            unanswered = sum(status(k, x) == "skipped" for k, x in enumerate(items))
            if unanswered > 0:
                S._show_submit_confirm = True
                st.rerun()
            else:
                S.finished = time.time()
                go("results")
    elif c2.button("Finish quiz" if last else "Next", type="primary", use_container_width=True,
                   icon=":material/check:" if last else ":material/arrow_forward:"):
        if last:
            S.finished = time.time()
            go("results")
        S.i += 1
        st.rerun()

    # Submit confirmation dialog for exam mode
    if S.mode == "Exam" and S.get("_show_submit_confirm"):
        unanswered = sum(status(k, x) == "skipped" for k, x in enumerate(items))
        flagged_count = len(S.get("flagged", set()))
        md(f'<div class="confirm-modal">'
           f'<h3>Submit exam?</h3>'
           f'<p>{unanswered} unanswered · {flagged_count} flagged for review</p>'
           f'</div>')
        cc1, cc2 = st.columns(2)
        if cc1.button("Go back", use_container_width=True):
            S._show_submit_confirm = False
            st.rerun()
        if cc2.button("Submit now", type="primary", use_container_width=True):
            S._show_submit_confirm = False
            S.finished = time.time()
            go("results")

    if last and S.mode != "Exam":
        left = sum(status(k, x) == "skipped" for k, x in enumerate(items))
        if left:
            st.caption(f"{left} question{'s' if left > 1 else ''} unanswered.")


def screen_results():
    right, total = tally()
    wrong = total - right
    secs = int((S.finished or time.time()) - S.started)
    pct = round(100 * right / total) if total else None
    head = ("Quiz complete." if pct is None else
            "Excellent recall." if pct >= 90 else
            "Strong recall." if pct >= 80 else
            "Getting there." if pct >= 50 else
            "Worth another pass.")

    # Retry round indicator
    retry = S.get("retry_round", 0)
    retry_badge = f' · Retry round {retry}' if retry > 0 else ''

    md('<div class="brand"><span class="mark"></span>Recall</div>'
       f'<p class="eyebrow">{S.difficulty} · {S.mode} mode{retry_badge}</p><h1 class="display">{head}</h1>')

    # Metric cards row
    if total:
        md(f'<div class="metrics-row">'
           f'<div class="metric-card"><div class="metric-value">{pct}%</div><div class="metric-label">Score</div></div>'
           f'<div class="metric-card"><div class="metric-value">{right}/{total}</div><div class="metric-label">MCQ Correct</div></div>'
           f'<div class="metric-card"><div class="metric-value">{secs // 60}:{secs % 60:02d}</div><div class="metric-label">Time</div></div>'
           f'<div class="metric-card"><div class="metric-value">{len(S.qs)}</div><div class="metric-label">Questions</div></div>'
           f'</div>')

        # Large score display
        md(f'<div class="score">{right}<small> / {total}</small></div>'
           f'<p class="meta"><b>{pct}%</b> · {right} correct · {wrong} to review · {secs // 60}m {secs % 60:02d}s</p>')
    else:
        md('<p class="meta">This quiz had no multiple-choice questions, so there is no automatic score. '
           'Compare your answers with the model answers in the review.</p>')

    # Per-question result strip
    cells = "".join(f'<i class="{status(i, q)}" title="Question {i + 1}"></i>' for i, q in enumerate(S.qs))
    md(f'<div class="strip" aria-label="Per-question result">{cells}</div>')

    # Per-type breakdown
    type_counts = {}
    for i, q in enumerate(S.qs):
        t = q["type"]
        s = status(i, q)
        if t not in type_counts:
            type_counts[t] = {"total": 0, "correct": 0}
        type_counts[t]["total"] += 1
        if s == "right" or (t != "mcq" and s == "open"):
            type_counts[t]["correct"] += 1
    if len(type_counts) > 1:
        breakdown = " · ".join(
            f'{TYPES.get(t, t)}: {c["correct"]}/{c["total"]}'
            for t, c in type_counts.items()
        )
        md(f'<p class="meta">{breakdown}</p>')

    # Action buttons
    c1, c2 = st.columns(2)
    if c1.button("Review mistakes", type="primary", use_container_width=True,
                 disabled=wrong == 0 and total > 0, icon=":material/rate_review:"):
        S.only_wrong = True
        go("review")
    if c2.button("Review all", use_container_width=True, icon=":material/list:"):
        S.only_wrong = False
        go("review")

    c3, c4 = st.columns(2)

    # Retry mistakes button — creates a mini quiz of only wrong/skipped MCQs
    wrong_items = [(i, q) for i, q in enumerate(S.qs) if q["type"] == "mcq" and status(i, q) in ("wrong", "skipped")]
    if c3.button(f"Retry {len(wrong_items)} mistakes", use_container_width=True,
                 disabled=len(wrong_items) == 0, type="primary"):
        retry_qs = [q for _, q in wrong_items]
        S.retry_round = S.get("retry_round", 0) + 1
        start_quiz(S.quiz, S.difficulty, "Practice", items_override=retry_qs)
        st.rerun()

    if c4.button("New quiz", use_container_width=True, icon=":material/add:"):
        go("setup")

    c5, c6 = st.columns(2)
    if c5.button("Retake full quiz", use_container_width=True, icon=":material/replay:"):
        S.retry_round = 0
        start_quiz(S.quiz, S.difficulty, S.mode)
        st.rerun()

    d1, d2 = st.columns(2)
    d1.download_button("Download JSON", json.dumps(S.quiz, indent=2), "quiz.json", use_container_width=True)
    d2.download_button("Download Markdown", to_markdown(S.quiz, S.difficulty), "quiz.md", use_container_width=True)


def screen_review():
    md(f'<p class="eyebrow">Review · {"mistakes only" if S.only_wrong else "all questions"}</p>')
    if st.button("Back to results", icon=":material/arrow_back:"):
        go("results")
    shown = 0
    labels = {"right": ("check", "Correct"), "wrong": ("x", "Incorrect"),
              "open": ("pen", "Self-check"), "skipped": ("minus", "Skipped")}
    for i, q in enumerate(S.qs):
        s = status(i, q)
        if S.only_wrong and not (q["type"] == "mcq" and s in ("wrong", "skipped")):
            continue
        shown += 1
        ic, lab = labels[s]
        ans = S.answers.get(i)
        body = (f'<span class="chip {s}">{icon(ic)}{lab}</span>'
                f'<p class="qtext" style="font-size:1.15rem;margin:.2rem 0">{i + 1}. {esc(q["question"])}</p>')
        if q["type"] == "mcq":
            body += f'<p><span class="k">Your answer</span><br>{esc(ans) if ans else "—"}</p>'
            if s != "right":
                body += f'<p><span class="k">Correct answer</span><br>{esc(correct_text(q))}</p>'
            body += f'<p>{esc(q.get("explanation", ""))}</p>'
            # Source quote
            if q.get("source_quote"):
                body += f'<div class="source-quote"><span class="k">Reference:</span> <em>{esc(q["source_quote"])}</em></div>'
            md(f'<div class="card">{body}</div>')
        elif q["type"] == "short":
            body += (f'<p><span class="k">Your answer</span><br>{esc(str(ans or "—"))}</p>'
                     f'<p><span class="k">Model answer</span><br>{esc(q["model_answer"])}</p>'
                     f'<p><span class="k">Key points</span><br>{esc("; ".join(q.get("key_points", [])))}</p>')
            # Show AI grade if available
            if i in S.get("short_grades", {}):
                grade = S.short_grades[i]
                body += f'<p><span class="k">AI Score</span><br><b>{grade.get("score", "?")}%</b> — {esc(grade.get("feedback", ""))}</p>'
            md(f'<div class="card">{body}</div>')
        else:
            md(f'<div class="card">{body}</div>')
            st.caption("Your code")
            st.code(str(ans or ""), language=q.get("language", "python").lower())
            st.caption("Solution")
            st.code(q["solution"], language=q.get("language", "python").lower())
            st.write(q.get("explanation", ""))
            # Show test results if available
            if i in S.get("code_results", {}):
                result = S.code_results[i]
                st.caption(f"Test results: {result['passed']}/{result['total']} passed")
    if not shown:
        st.success("Nothing to review. Every multiple-choice answer was correct.")


{"setup": screen_setup, "quiz": screen_quiz, "results": screen_results, "review": screen_review}[S.stage]()
