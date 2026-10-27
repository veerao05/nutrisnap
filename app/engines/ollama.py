"""Free, local food recognition with an open-source vision model via Ollama.

No API key and no cost: the model runs on this machine. Install Ollama
(https://ollama.com), then pull a vision model, e.g. `ollama pull qwen2.5vl:3b`.
Much less accurate than the hosted engines, especially on busy plates.

Settings: OLLAMA_MODEL (default qwen2.5vl:3b), OLLAMA_URL, OLLAMA_NUM_CTX,
OLLAMA_KEEP_ALIVE.
"""

import base64
import json
import os
import time
import urllib.error
import urllib.request

from ..detection import MAX_ITEMS, SCHEMA, SYSTEM, Detection, prepare_image, user_prompt
from .base import EngineError

NAME = "ollama"
LABEL = "Ollama (local)"
FREE = True

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
# Prompt (~2k tokens) + image must fit in the context window, or Ollama
# silently truncates the input and the model misreads the photo.
NUM_CTX = int(os.environ.get("OLLAMA_NUM_CTX", "8192"))
MAX_SIDE = 768  # ~750 image tokens for Qwen2.5-VL; plenty for food photos

# Small models keep "finding" more foods until they run out of tokens, which
# truncates the JSON. A hard item cap makes the grammar force them to stop.
_SCHEMA = {**SCHEMA, "properties": {
    **SCHEMA["properties"],
    "items": {**SCHEMA["properties"]["items"], "maxItems": min(MAX_ITEMS, 10)},
}}

# Small models also "find" food in anything when asked to list foods, so first
# ask a plain classification question with no food catalog in sight.
_GATE_SCHEMA = {
    "type": "object",
    "properties": {"category": {"type": "string", "enum": [
        "food_or_drink", "diagram_chart_or_screenshot", "document_or_text",
        "person", "animal", "landscape_or_sky", "object", "other"]}},
    "required": ["category"],
}
_GATE_PROMPT = ("What does this image mainly show? Pick the single best category. "
                "Only choose food_or_drink if real food or drink is clearly visible.")


def model() -> str:
    return os.environ.get("OLLAMA_MODEL", "qwen2.5vl:3b")


def setup_hint() -> str:
    return f"install Ollama, run `ollama pull {model()}`, and keep Ollama running."


def _post(path: str, payload: dict | None = None, timeout: float = 300) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"{OLLAMA_URL}{path}", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


_last_seen = 0.0  # time the model was last confirmed installed


def available() -> bool:
    """True if Ollama is running and the vision model has been pulled.

    Once seen, stays True for 10 minutes: Ollama can be slow to answer while
    it's busy analysing, and that must not make the app report no engine.
    """
    global _last_seen
    if time.time() - _last_seen < 600:
        return True
    try:
        tags = _post("/api/tags", timeout=10)
    except (urllib.error.URLError, OSError, ValueError):
        return False
    names = {m["name"] for m in tags.get("models", [])}
    if model() in names or f"{model()}:latest" in names:
        _last_seen = time.time()
        return True
    return False


def _chat(messages: list[dict], schema: dict) -> dict:
    try:
        result = _post("/api/chat", {
            "model": model(),
            "stream": False,
            "format": schema,  # Ollama constrains output to this JSON schema
            # num_predict caps runaway generation (small models can loop).
            "options": {"temperature": 0, "num_ctx": NUM_CTX, "num_predict": 1500},
            # Unload the model from memory shortly after use to keep RAM free.
            "keep_alive": os.environ.get("OLLAMA_KEEP_ALIVE", "2m"),
            "messages": messages,
        })
    except urllib.error.HTTPError as e:
        raise EngineError(f"Ollama error ({e.code}): {e.read().decode()[:200]}", 502)
    except (urllib.error.URLError, OSError) as e:
        raise EngineError(f"Couldn't reach Ollama at {OLLAMA_URL}: {e}", 503)
    try:
        return json.loads(result["message"]["content"])
    except (KeyError, ValueError):
        raise ValueError("unreadable JSON")


def analyze(image_bytes: bytes, media_type: str, hint: str = "") -> Detection:
    image_b64 = base64.standard_b64encode(prepare_image(image_bytes, MAX_SIDE)).decode()

    try:
        gate = _chat([{"role": "user", "content": _GATE_PROMPT, "images": [image_b64]}],
                     _GATE_SCHEMA)
    except ValueError:
        gate = {"category": "food_or_drink"}  # can't tell; let the main pass decide
    category = gate.get("category", "other")
    if category != "food_or_drink":
        return Detection(is_food=False, items=[],
                         notes=f"Looks like: {category.replace('_', ' ')}.")

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_prompt(hint) + " Reply with JSON only.",
         "images": [image_b64]},
    ]
    for _ in range(2):  # small models occasionally emit broken JSON
        try:
            return Detection.model_validate(_chat(messages, _SCHEMA))
        except ValueError:
            continue
    raise EngineError("The local model returned an unreadable answer; try again.", 502)
