# NutriSnap — AI Food & Calorie Tracker

Snap a meal photo → recognise dishes → estimate portions → calories & macros → see how much more to eat today.

## How it works

| Piece | File | What it does |
|---|---|---|
| Vision engines (pluggable) | `app/engines/` | One file per AI provider, all with the same interface; recognise dishes + estimate grams |
| Shared prompt & schema | `app/detection.py` | The instructions, JSON schema and image resizing every engine uses |
| Nutrition database | `app/nutrition_db.py` | ~90 foods (incl. Indian dishes), kcal/protein/carbs/fat per 100 g |
| Daily-goal logic | `app/tracker.py` | Macro targets, remaining kcal/macros, rest-of-day advice |
| API | `app/main.py` | FastAPI: `POST /api/analyze`, `GET /api/engines`, `POST /api/meals`, `DELETE /api/meals/{id}`, `GET /api/today`, `PUT /api/goal` |
| Storage | `app/storage.py` | SQLite (`nutrisnap.db`) |
| UI | `app/static/index.html` | Camera upload, engine picker, editable portions, calorie ring, macro bars, goal calculator |
| Tests | `tests/test_app.py` | `.venv/bin/python -m pytest -q` (fake engine; no keys needed) |

## Run

```bash
uv venv && uv pip install -r requirements.txt
export GEMINI_API_KEY=...          # and/or any engine settings below
.venv/bin/uvicorn app.main:app --port 8001 --reload
```

Open http://localhost:8001. API docs: http://localhost:8001/docs

## Vision engines

Set up any number; pick one in the page's **Analysis engine** dropdown, per request
with the `engine` form field, or as the default with `NUTRISNAP_VISION=<name>`.
With nothing chosen, the first one that's set up wins (in this order):

| Engine (`name`) | Cost | Setup | Model setting |
|---|---|---|---|
| Claude (`claude`) | Paid per photo | `ANTHROPIC_API_KEY` from console.anthropic.com | `NUTRISNAP_CLAUDE_MODEL` (default `claude-opus-5-5`; `claude-sonnet-5-5` is cheaper) |
| Gemini (`gemini`) | Free tier (daily limits) | `GEMINI_API_KEY` from aistudio.google.com/apikey | `GEMINI_MODEL` (default `gemini-2.5-flash`) |
| OpenAI-compatible (`openai_compat`) | Depends on provider | `OPENAI_COMPAT_BASE_URL`, `OPENAI_COMPAT_API_KEY`, `OPENAI_COMPAT_MODEL` | Groq: `https://api.groq.com/openai/v1` · OpenRouter: `https://openrouter.ai/api/v1` · LM Studio: `http://localhost:1234/v1` |
| Ollama (`ollama`) | Free, local | Install Ollama, `ollama pull qwen2.5vl:3b` | `OLLAMA_MODEL` |

Adding another provider: create `app/engines/<name>.py` with `NAME`, `LABEL`, `FREE`,
`model()`, `available()`, `setup_hint()` and `analyze()`, then add it to `ENGINES`
in `app/engines/__init__.py`.

Accuracy notes: Claude and Gemini handle multi-dish plates well. Small local models
(qwen2.5vl:3b) often invent or repeat dishes on busy plates like a thali; use the
note box to name the dishes and let the model estimate portions.
