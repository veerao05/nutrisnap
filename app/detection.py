"""What every vision engine returns, plus the prompt and schema they share.

Each engine identifies the dishes in a photo, estimates grams on the plate,
and maps each dish to a key in the local nutrition database. The backend then
computes calories/macros from the database, so numbers stay consistent across
engines; an engine's own per-100 g estimate is only used when a dish isn't in
the DB.
"""

from io import BytesIO

from PIL import Image, ImageOps
from pydantic import BaseModel

from .nutrition_db import catalog_for_prompt

MAX_ITEMS = 12


class DetectedItem(BaseModel):
    name: str
    db_key: str | None
    grams: float
    confidence: float
    est_kcal_per_100g: float
    est_protein_per_100g: float
    est_carbs_per_100g: float
    est_fat_per_100g: float


class Detection(BaseModel):
    is_food: bool
    items: list[DetectedItem]
    notes: str


_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "db_key": {"type": ["string", "null"]},
        "grams": {"type": "number"},
        "confidence": {"type": "number"},
        "est_kcal_per_100g": {"type": "number"},
        "est_protein_per_100g": {"type": "number"},
        "est_carbs_per_100g": {"type": "number"},
        "est_fat_per_100g": {"type": "number"},
    },
    "required": list(DetectedItem.model_fields),
    "additionalProperties": False,
}

SCHEMA = {
    "type": "object",
    "properties": {
        "is_food": {"type": "boolean"},
        "items": {"type": "array", "items": _ITEM_SCHEMA},
        "notes": {"type": "string"},
    },
    "required": ["is_food", "items", "notes"],
    "additionalProperties": False,
}

SYSTEM = f"""You are the food-recognition engine of a calorie-tracking app.
Given a meal photo, identify every distinct food item and estimate the portion
actually on the plate, in grams (as served, cooked weight).

Portion estimation: use visual references - plate diameter (a standard dinner
plate is ~26 cm), bowl size, cutlery, hands, packaging - and typical food
densities. A heaped cup of cooked rice is ~200 g; one roti ~40 g; one egg ~50 g;
a chicken breast ~170 g; a small katori (bowl) holds ~100-150 g.

List each distinct item once (at most {MAX_ITEMS}); never list foods you can't
actually see. For each item set db_key to the closest match from the catalog
below, or null if nothing is a reasonable match. Always also fill the
est_*_per_100g fields with your own best estimate, used as a fallback when
db_key is null. confidence is 0-1 for the identification. If the photo
contains no real food (a diagram, screenshot, person, landscape...), set
is_food to false and return an empty items list. Use notes for one short
sentence on anything that affects accuracy (hidden oil, sauces, partial view).

Catalog (key: description):
{catalog_for_prompt()}"""


def user_prompt(hint: str = "") -> str:
    text = "Identify the foods and estimate portions."
    if hint:
        text += f" The user adds: {hint}"
    return text


def prepare_image(image_bytes: bytes, max_side: int) -> bytes:
    """Fix phone-photo rotation and shrink: fewer tokens, faster, cheaper."""
    img = ImageOps.exif_transpose(Image.open(BytesIO(image_bytes))).convert("RGB")
    img.thumbnail((max_side, max_side))
    out = BytesIO()
    img.save(out, "JPEG", quality=90)
    return out.getvalue()
