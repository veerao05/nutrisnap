"""Local nutrition database: values per 100 g of the food as served.

Figures are rounded approximations based on USDA FoodData Central entries
(and common recipe averages for mixed dishes). Swap in a fuller dataset or
the FoodData Central API for production use.
"""

# key: (display name, kcal, protein g, carbs g, fat g) per 100 g
FOODS: dict[str, tuple[str, float, float, float, float]] = {
    # Grains & staples
    "white_rice_cooked": ("White rice, cooked", 130, 2.7, 28.2, 0.3),
    "brown_rice_cooked": ("Brown rice, cooked", 123, 2.7, 25.6, 1.0),
    "basmati_rice_cooked": ("Basmati rice, cooked", 121, 3.5, 25.2, 0.4),
    "jeera_rice": ("Jeera rice", 160, 3.0, 28.0, 4.0),
    "biryani_chicken": ("Chicken biryani", 180, 8.5, 22.0, 6.5),
    "biryani_veg": ("Vegetable biryani", 155, 3.5, 25.0, 4.8),
    "pasta_cooked": ("Pasta, cooked", 158, 5.8, 30.9, 0.9),
    "spaghetti_bolognese": ("Spaghetti bolognese", 135, 7.0, 16.0, 4.5),
    "bread_white": ("White bread", 265, 9.0, 49.0, 3.2),
    "bread_wholewheat": ("Whole-wheat bread", 252, 12.4, 42.7, 3.5),
    "roti_chapati": ("Roti / chapati", 297, 9.8, 51.0, 7.5),
    "naan": ("Naan", 310, 9.0, 50.0, 7.5),
    "paratha": ("Plain paratha", 326, 6.4, 45.0, 13.5),
    "dosa_plain": ("Plain dosa", 168, 3.9, 29.0, 3.7),
    "masala_dosa": ("Masala dosa", 180, 3.8, 27.0, 6.5),
    "idli": ("Idli", 135, 4.0, 28.0, 0.5),
    "poha": ("Poha", 130, 2.6, 23.0, 3.2),
    "upma": ("Upma", 145, 3.5, 21.0, 5.2),
    "oats_cooked": ("Oatmeal, cooked", 71, 2.5, 12.0, 1.5),
    "quinoa_cooked": ("Quinoa, cooked", 120, 4.4, 21.3, 1.9),
    "potato_boiled": ("Potato, boiled", 87, 1.9, 20.1, 0.1),
    "french_fries": ("French fries", 312, 3.4, 41.0, 15.0),
    # Protein
    "chicken_breast_grilled": ("Chicken breast, grilled", 165, 31.0, 0.0, 3.6),
    "chicken_curry": ("Chicken curry", 150, 13.0, 5.0, 9.0),
    "butter_chicken": ("Butter chicken", 190, 12.5, 6.0, 13.0),
    "chicken_tikka": ("Chicken tikka", 150, 22.0, 3.0, 5.5),
    "tandoori_chicken": ("Tandoori chicken", 160, 24.0, 2.5, 6.0),
    "fried_chicken": ("Fried chicken", 260, 22.0, 9.0, 15.0),
    "beef_steak": ("Beef steak, grilled", 250, 26.0, 0.0, 16.0),
    "beef_burger_patty": ("Beef burger patty", 254, 17.0, 0.0, 20.0),
    "salmon_cooked": ("Salmon, cooked", 206, 22.0, 0.0, 12.0),
    "fish_curry": ("Fish curry", 125, 12.0, 4.0, 7.0),
    "shrimp_cooked": ("Shrimp, cooked", 99, 24.0, 0.2, 0.3),
    "egg_boiled": ("Egg, boiled", 155, 12.6, 1.1, 10.6),
    "egg_omelette": ("Omelette", 154, 10.6, 0.6, 12.0),
    "tofu": ("Tofu", 76, 8.0, 1.9, 4.8),
    "paneer": ("Paneer", 265, 18.3, 1.2, 20.8),
    "palak_paneer": ("Palak paneer", 145, 7.0, 6.0, 10.5),
    "paneer_butter_masala": ("Paneer butter masala", 210, 8.0, 8.0, 16.5),
    "dal_tadka": ("Dal tadka", 116, 6.0, 15.0, 3.8),
    "dal_makhani": ("Dal makhani", 145, 6.0, 14.0, 7.5),
    "chana_masala": ("Chana masala", 140, 6.5, 18.0, 5.0),
    "rajma": ("Rajma curry", 125, 6.3, 17.0, 3.8),
    "sambar": ("Sambar", 65, 3.0, 9.0, 2.0),
    "lentils_cooked": ("Lentils, cooked", 116, 9.0, 20.0, 0.4),
    "chickpeas_cooked": ("Chickpeas, cooked", 164, 8.9, 27.4, 2.6),
    "greek_yogurt": ("Greek yogurt, plain", 97, 9.0, 3.9, 5.0),
    "curd_yogurt": ("Curd / yogurt, plain", 61, 3.5, 4.7, 3.3),
    "raita": ("Raita", 65, 3.0, 5.0, 3.5),
    # Vegetables & salads
    "green_salad": ("Green salad (no dressing)", 17, 1.2, 3.3, 0.2),
    "caesar_salad": ("Caesar salad", 170, 5.0, 7.0, 14.0),
    "mixed_veg_curry": ("Mixed vegetable curry", 95, 2.5, 9.0, 5.5),
    # South Indian meals / thali components
    "avial": ("Avial", 110, 2.5, 8.0, 7.5),
    "kootu": ("Kootu (vegetable-lentil)", 95, 4.0, 10.0, 4.5),
    "beans_poriyal": ("Beans poriyal", 85, 2.5, 8.0, 5.0),
    "cabbage_poriyal": ("Cabbage poriyal", 75, 2.0, 7.0, 4.5),
    "carrot_poriyal": ("Carrot poriyal", 80, 1.2, 9.0, 4.5),
    "potato_fry": ("Potato fry / roast", 150, 2.5, 20.0, 7.0),
    "rasam": ("Rasam", 30, 1.0, 4.0, 1.2),
    "kadhi": ("Kadhi / mor kuzhambu", 85, 3.0, 7.0, 5.0),
    "kosambari": ("Kosambari (lentil salad)", 80, 4.0, 9.0, 3.0),
    "curd_rice": ("Curd rice", 110, 3.0, 15.0, 4.0),
    "lemon_rice": ("Lemon rice", 175, 3.0, 28.0, 5.5),
    "pongal": ("Ven pongal", 150, 4.0, 20.0, 5.5),
    "medu_vada": ("Medu vada", 300, 9.0, 30.0, 16.0),
    "papad_fried": ("Papad / appalam, fried", 450, 17.0, 42.0, 24.0),
    "payasam": ("Payasam", 150, 3.5, 23.0, 5.0),
    "aloo_gobi": ("Aloo gobi", 105, 2.5, 12.0, 5.5),
    "bhindi_masala": ("Bhindi masala", 110, 2.5, 9.0, 7.5),
    "broccoli_steamed": ("Broccoli, steamed", 35, 2.4, 7.2, 0.4),
    "stir_fry_vegetables": ("Stir-fried vegetables", 80, 2.5, 8.0, 4.5),
    "avocado": ("Avocado", 160, 2.0, 8.5, 14.7),
    # Fast food & snacks
    "pizza_cheese": ("Cheese pizza", 266, 11.4, 33.0, 10.0),
    "pizza_pepperoni": ("Pepperoni pizza", 298, 12.5, 32.0, 13.0),
    "burger": ("Hamburger (whole)", 250, 13.0, 30.0, 9.0),
    "sandwich_chicken": ("Chicken sandwich", 230, 14.0, 24.0, 8.5),
    "wrap_chicken": ("Chicken wrap", 210, 12.0, 22.0, 8.0),
    "sushi_roll": ("Sushi roll", 150, 5.5, 29.0, 1.2),
    "fried_rice": ("Fried rice", 163, 4.5, 27.0, 4.2),
    "noodles_chow_mein": ("Chow mein noodles", 170, 5.5, 24.0, 6.0),
    "samosa": ("Samosa", 262, 4.6, 29.0, 14.5),
    "pakora": ("Pakora", 280, 6.5, 26.0, 17.0),
    "pav_bhaji": ("Pav bhaji", 185, 4.5, 26.0, 7.0),
    "chole_bhature": ("Chole bhature", 290, 7.5, 33.0, 14.5),
    "nachos": ("Nachos with cheese", 306, 8.0, 32.0, 17.0),
    # Fruit
    "apple": ("Apple", 52, 0.3, 13.8, 0.2),
    "banana": ("Banana", 89, 1.1, 22.8, 0.3),
    "orange": ("Orange", 47, 0.9, 11.8, 0.1),
    "mango": ("Mango", 60, 0.8, 15.0, 0.4),
    "grapes": ("Grapes", 69, 0.7, 18.1, 0.2),
    "berries_mixed": ("Mixed berries", 50, 0.9, 12.0, 0.3),
    "fruit_salad": ("Fruit salad", 55, 0.7, 14.0, 0.2),
    # Breakfast & dairy
    "pancakes": ("Pancakes", 227, 6.4, 28.0, 9.7),
    "granola": ("Granola", 471, 10.0, 64.0, 20.0),
    "cereal_with_milk": ("Cereal with milk", 110, 3.5, 20.0, 2.0),
    "milk_whole": ("Whole milk", 61, 3.2, 4.8, 3.3),
    "cheese_cheddar": ("Cheddar cheese", 403, 25.0, 1.3, 33.0),
    "peanut_butter": ("Peanut butter", 588, 25.0, 20.0, 50.0),
    # Desserts
    "gulab_jamun": ("Gulab jamun", 320, 4.5, 50.0, 12.0),
    "ice_cream": ("Ice cream", 207, 3.5, 24.0, 11.0),
    "chocolate_cake": ("Chocolate cake", 371, 5.3, 53.0, 15.0),
    "cookie": ("Cookie", 488, 5.0, 64.0, 24.0),
    "kheer": ("Kheer / rice pudding", 140, 3.8, 21.0, 4.5),
}


def lookup(key: str | None):
    """Return (name, kcal, protein, carbs, fat) per 100 g, or None."""
    if not key:
        return None
    return FOODS.get(key)


def _norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


_BY_NAME = {}
for _k, _v in FOODS.items():
    _BY_NAME[_norm(_k)] = _k
    _BY_NAME[_norm(_v[0])] = _k


def resolve_key(db_key: str | None, name: str) -> str | None:
    """Best catalog key for an item: the model's key if valid, else match by name."""
    if db_key in FOODS:
        return db_key
    for candidate in (db_key or "", name):
        key = _BY_NAME.get(_norm(candidate))
        if key:
            return key
    return None


def all_foods() -> list[dict]:
    return [{"key": k, "name": v[0], "per100": {"calories": v[1], "protein": v[2],
             "carbs": v[3], "fat": v[4]}} for k, v in sorted(FOODS.items(), key=lambda kv: kv[1][0])]


def catalog_for_prompt() -> str:
    """Compact key list the vision model picks matches from."""
    return "\n".join(f"{k}: {v[0]}" for k, v in FOODS.items())
