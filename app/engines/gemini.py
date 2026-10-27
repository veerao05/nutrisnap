"""Google Gemini vision. Has a free tier with daily limits (aistudio.google.com).

Setup: export GEMINI_API_KEY=...   (free key from aistudio.google.com/apikey)
Model: GEMINI_MODEL (default gemini-2.5-flash)
Note: on Google's free tier, your inputs may be used to improve Google products.
"""

import copy
import json
import os

from ..detection import SCHEMA, SYSTEM, Detection, prepare_image, user_prompt
from .base import EngineError

NAME = "gemini"
LABEL = "Gemini"
FREE = True  # free tier, rate-limited

_client = None


def model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def available() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def setup_hint() -> str:
    return "set GEMINI_API_KEY (free at aistudio.google.com/apikey) and restart the server."


def _gemini_schema() -> dict:
    """Gemini's schema support is narrower: no additionalProperties, no type lists."""
    schema = copy.deepcopy(SCHEMA)
    schema.pop("additionalProperties", None)
    item = schema["properties"]["items"]["items"]
    item.pop("additionalProperties", None)
    item["properties"]["db_key"] = {
        "type": "string", "description": "catalog key, or empty string if no match"}
    return schema


def analyze(image_bytes: bytes, media_type: str, hint: str = "") -> Detection:
    from google import genai  # imported lazily: only needed when Gemini is used
    from google.genai import errors, types

    global _client
    if _client is None:
        _client = genai.Client()  # reads GEMINI_API_KEY / GOOGLE_API_KEY

    image = prepare_image(image_bytes, 1536)
    try:
        response = _client.models.generate_content(
            model=model(),
            contents=[types.Part.from_bytes(data=image, mime_type="image/jpeg"),
                      user_prompt(hint)],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM,
                response_mime_type="application/json",
                response_json_schema=_gemini_schema(),
                temperature=0,
                max_output_tokens=8192,
            ),
        )
    except errors.ClientError as e:
        if e.code == 429:
            raise EngineError("Gemini free-tier limit reached; wait a bit and retry.", 429)
        raise EngineError(f"Gemini error ({e.code}): {e.message}", 502)
    except errors.APIError as e:
        raise EngineError(f"Gemini server error ({e.code}); try again.", 502)

    if not response.text:
        raise EngineError("Gemini returned no answer (it may have blocked the image).", 422)
    try:
        data = json.loads(response.text)
    except ValueError:
        raise EngineError("Gemini returned an unreadable answer; try again.", 502)
    for item in data.get("items", []):
        item["db_key"] = item.get("db_key") or None  # "" -> no match
    try:
        return Detection.model_validate(data)
    except ValueError:
        raise EngineError("Gemini's answer was missing fields; try again.", 502)
