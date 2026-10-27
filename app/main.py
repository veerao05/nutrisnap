"""NutriSnap FastAPI backend."""

from datetime import date
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import engines, nutrition_db, storage, tracker

STATIC = Path(__file__).parent / "static"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_BYTES = 15 * 1024 * 1024  # engines downscale before sending

app = FastAPI(title="NutriSnap", version="1.0")
storage.init()


class Goal(BaseModel):
    calories: int = Field(ge=800, le=6000)
    protein_pct: int = Field(ge=5, le=70)
    carbs_pct: int = Field(ge=5, le=80)
    fat_pct: int = Field(ge=5, le=70)


class Per100(BaseModel):
    calories: float
    protein: float
    carbs: float
    fat: float


class MealItem(BaseModel):
    name: str
    grams: float = Field(ge=0, le=5000)
    per100: Per100
    db_key: str | None = None
    source: str = "database"


class NewMeal(BaseModel):
    label: str = "Meal"
    items: list[MealItem]


def _day_summary() -> dict:
    meals = storage.meals_for(date.today())
    goal = storage.get_goal()
    target = tracker.targets(goal)
    consumed = {k: round(sum(m[k] for m in meals), 1)
                for k in ("calories", "protein", "carbs", "fat")}
    return {
        "date": date.today().isoformat(),
        "goal": goal,
        "target": target,
        "consumed": consumed,
        "guidance": tracker.guidance(consumed, target),
        "meals": meals,
    }


@app.post("/api/analyze")
async def analyze(image: UploadFile = File(...), hint: str = Form(""),
                  engine: str = Form("")):
    """Recognise foods in a photo and estimate nutrition. Does not save.

    `engine` picks the vision engine (see GET /api/engines); blank = default.
    """
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Upload a JPEG, PNG, WebP or GIF image.")
    data = await image.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Image must be under 15 MB.")

    try:
        chosen = engines.choose(engine)
        detection = chosen.analyze(data, image.content_type, hint.strip()[:300])
    except engines.EngineError as e:
        raise HTTPException(e.status_code, str(e))
    except OSError:  # Pillow couldn't read the file
        raise HTTPException(415, "That file couldn't be read as an image.")

    if not detection.is_food or not detection.items:
        seen = f" {detection.notes}" if detection.notes.startswith("Looks like") else ""
        raise HTTPException(422, f"No food detected in that photo.{seen}")

    items = tracker.compute_items(detection)
    meal_totals = tracker.totals(items)
    day = _day_summary()
    projected = {k: day["consumed"][k] + meal_totals[k] for k in meal_totals}
    return {
        "items": items,
        "totals": meal_totals,
        "notes": detection.notes,
        "engine": {"name": chosen.NAME, "label": chosen.LABEL, "model": chosen.model()},
        "projected_guidance": tracker.guidance(projected, day["target"]),
    }


@app.post("/api/meals")
def log_meal(meal: NewMeal):
    items = []
    for it in meal.items:
        k = it.grams / 100
        items.append({
            "name": it.name, "grams": round(it.grams), "db_key": it.db_key,
            "source": it.source, "per100": it.per100.model_dump(),
            "calories": round(it.per100.calories * k),
            "protein": round(it.per100.protein * k, 1),
            "carbs": round(it.per100.carbs * k, 1),
            "fat": round(it.per100.fat * k, 1),
        })
    if not items:
        raise HTTPException(400, "A meal needs at least one item.")
    storage.add_meal(meal.label.strip()[:40] or "Meal", items, tracker.totals(items))
    return _day_summary()


@app.delete("/api/meals/{meal_id}")
def remove_meal(meal_id: int):
    if not storage.delete_meal(meal_id):
        raise HTTPException(404, "Meal not found.")
    return _day_summary()


@app.get("/api/foods")
def list_foods():
    """Nutrition database entries, for correcting or adding items."""
    return nutrition_db.all_foods()


@app.get("/api/engines")
def list_engines():
    return {"default": engines.default_name(), "engines": engines.describe()}


@app.get("/api/today")
def today():
    return _day_summary()


@app.put("/api/goal")
def update_goal(goal: Goal):
    if goal.protein_pct + goal.carbs_pct + goal.fat_pct != 100:
        raise HTTPException(400, "Macro percentages must add up to 100.")
    storage.set_goal(goal.model_dump())
    return _day_summary()


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
