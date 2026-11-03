# Recall · AI Quiz Studio

Turn **any topic** or **your own documents** (PDF / DOCX / PPTX / TXT / MD) into a quiz with
multiple-choice, written and coding questions, at Easy / Medium / Hard difficulty.

## What's new in this version
- A new website (Flask + HTML/CSS/JS) with a glass, deep-violet look. It replaces the Streamlit UI.
- **Topic quizzes:** type any topic and the app researches it on the web (Wikipedia + DuckDuckGo,
  plus Tavily if you add a key), then writes questions from those sources. Sources are listed on the results page.
- Practice mode (instant feedback) and Exam mode (timer, question grid, flag for review).
- AI grading for written answers. Live test running for Python coding questions.
- Retry-mistakes loop, history and stats (saved in your browser), JSON/Markdown export, keyboard shortcuts.

## Run it (one-click)
- Double-click **`run_recall.bat`** in the project folder to create the virtual environment,
  install dependencies, start the app and open **http://localhost:8000** in your browser.
- Double-click **`open_in_vscode.bat`** to open the project in VS Code, where you can press
  **F5** and choose **Run Recall website** or run the task **Run Recall (browser)**.

## Run it (manual / VS Code terminal)
```bash
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env   (then add your GROQ_API_KEY)
python -m recall.server
```
Then open **http://localhost:8000**.
In VS Code you can also press **F5** and pick "Run Recall website".

## AI engines
- **Groq Cloud**: used automatically when `GROQ_API_KEY` (starting with `gsk_`) is in `.env`.
- **Ollama (local, offline)**: fallback. Install Ollama, then run `ollama pull llama3.2:3b`.
Choose the engine in the right-hand panel or in Settings.

## Project structure
```
recall/            Flask server + backend
  server.py        web server + JSON API
  quiz_engine.py   prompts, LLM calls (Groq / Ollama), JSON validation, topic quizzes
  research.py      web research for topic quizzes (Wikipedia, DuckDuckGo, Tavily)
  file_loader.py   text extraction from PDF / DOCX / PPTX / TXT / MD
  sandbox.py       runs Python code against test cases
  static/          the website: index.html, styles.css, app.js
legacy_streamlit/  old Streamlit UI (streamlit run legacy_streamlit/app.py)
scripts/           run.bat / run.sh launchers
docs/report/       project report (LaTeX)
```

## API
| Method | Path | Body |
|---|---|---|
| GET | `/api/status` | – |
| POST | `/api/quiz/topic` | `{topic, use_web, depth, difficulty, n_mcq, n_short, n_code, language, engine}` |
| POST | `/api/quiz/document` | multipart: `files[]`, `text`, `settings` (JSON) |
| POST | `/api/grade` | `{answer, model_answer, key_points}` |
| POST | `/api/run` | `{code, test_cases, language}` |

## Notes
- If the web can't be reached, topic quizzes still work using the AI's own knowledge (you'll see a notice).
- The code runner executes code on your own machine; it is meant for local use only.
