"""Nutrition maths: per-item macros, daily targets and rest-of-day guidance."""

from datetime import datetime

from .nutrition_db import FOODS, lookup, resolve_key
from .detection import Detection


def compute_items(detection: Detection) -> list[dict]:
    """Turn detected items + grams into calories/macros using the nutrition DB."""
    out = []
    for it in detection.items:
        grams = max(it.grams, 0)
        key = resolve_key(it.db_key, it.name)
        ref = lookup(key)
        if ref:
            _, kcal, p, c, f = ref
            source = "database"
        else:
            kcal, p, c, f = (it.est_kcal_per_100g, it.est_protein_per_100g,
                             it.est_carbs_per_100g, it.est_fat_per_100g)
            source = "model estimate"
        k = grams / 100
        name = it.name.strip()
        if ref and (not name or name == key or "_" in name):
            name = ref[0]  # model echoed the catalog key; show the readable name
        out.append({
            "name": name,
            "db_key": key if ref else None,
            "grams": round(grams),
            "confidence": round(it.confidence, 2),
            "source": source,
            "per100": {"calories": kcal, "protein": p, "carbs": c, "fat": f},
            "calories": round(kcal * k),
            "protein": round(p * k, 1),
            "carbs": round(c * k, 1),
            "fat": round(f * k, 1),
        })
    return out


def totals(items: list[dict]) -> dict:
    return {
        "calories": round(sum(i["calories"] for i in items)),
        "protein": round(sum(i["protein"] for i in items), 1),
        "carbs": round(sum(i["carbs"] for i in items), 1),
        "fat": round(sum(i["fat"] for i in items), 1),
    }


def targets(goal: dict) -> dict:
    kcal = goal["calories"]
    return {
        "calories": kcal,
        "protein": round(kcal * goal["protein_pct"] / 100 / 4),
        "carbs": round(kcal * goal["carbs_pct"] / 100 / 4),
        "fat": round(kcal * goal["fat_pct"] / 100 / 9),
    }


def _meals_left(now: datetime) -> int:
    h = now.hour
    if h < 11:
        return 3  # lunch, snack, dinner
    if h < 16:
        return 2  # snack, dinner
    if h < 21:
        return 1  # dinner
    return 0


def _protein_dense_picks(limit: int = 3) -> list[str]:
    ranked = sorted(FOODS.values(), key=lambda v: v[2] / max(v[1], 1), reverse=True)
    return [v[0] for v in ranked[:limit]]


def guidance(consumed: dict, target: dict, now: datetime | None = None) -> dict:
    """How much more to eat for the rest of the day, and how to split it."""
    now = now or datetime.now()
    remaining = {k: round(target[k] - consumed[k], 1) for k in target}
    remaining["calories"] = round(remaining["calories"])
    meals_left = _meals_left(now)
    pct = consumed["calories"] / target["calories"] * 100 if target["calories"] else 0

    tips = []
    rk = remaining["calories"]
    if consumed["calories"] == 0:
        return {
            "status": "empty",
            "percent_of_goal": 0,
            "remaining": remaining,
            "meals_left": meals_left,
            "headline": f"Nothing logged yet. Your goal today is {target['calories']} kcal.",
            "tips": ["Snap a photo of your next meal to start tracking."],
        }
    if rk < -150:
        status = "over"
        headline = f"You're {-rk} kcal over today's goal."
        tips.append("Keep any remaining meals light: vegetables, salad, or a clear soup.")
    elif rk <= 150:
        status = "on_target"
        headline = "You've hit today's calorie goal."
        if meals_left:
            tips.append("If you're still hungry, choose low-calorie, high-volume foods.")
    else:
        status = "under"
        if meals_left:
            per_meal = round(rk / meals_left)
            headline = (f"Eat about {rk} kcal more today - roughly {per_meal} kcal "
                        f"across each of your {meals_left} remaining meal"
                        f"{'s' if meals_left > 1 else ''}.")
        elif rk <= 400:
            headline = f"You're {rk} kcal under goal. A small snack would close the gap."
        else:
            headline = (f"You're {rk} kcal under goal. If you're hungry, have a balanced "
                        "meal; otherwise no need to force it this late.")

    if remaining["protein"] > 15 and status != "over":
        tips.append(f"You still need ~{remaining['protein']:.0f} g protein. Good picks: "
                    + ", ".join(_protein_dense_picks()) + ".")
    if remaining["fat"] < -5:
        tips.append("Fat is already above target, so go easy on oil, butter and fried food.")
    if remaining["carbs"] < -10:
        tips.append("Carbs are above target; favour protein and vegetables next.")

    return {
        "status": status,
        "percent_of_goal": round(pct),
        "remaining": remaining,
        "meals_left": meals_left,
        "headline": headline,
        "tips": tips,
    }
