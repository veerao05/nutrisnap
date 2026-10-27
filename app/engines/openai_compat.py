"""Any provider with an OpenAI-compatible chat API and a vision model.

One engine covers many services; point it at one with three settings:

    OPENAI_COMPAT_BASE_URL   e.g. https://api.groq.com/openai/v1      (Groq, free tier)
                                  https://openrouter.ai/api/v1         (OpenRouter)
                                  http://localhost:1234/v1             (LM Studio, local)
    OPENAI_COMPAT_API_KEY    the provider's key (any text for local servers)
    OPENAI_COMPAT_MODEL      a vision-capable model name on that provider
    OPENAI_COMPAT_LABEL      optional display name, e.g. "Groq"

Check the provider's model list for a current vision model; names change often.
"""

import base64
import json
import os
import urllib.error
import urllib.request

from ..detection import SCHEMA, SYSTEM, Detection, prepare_image, user_prompt
from .base import EngineError

NAME = "openai_compat"
LABEL = os.environ.get("OPENAI_COMPAT_LABEL", "OpenAI-compatible")
FREE = False  # depends on the provider


def model() -> str:
    return os.environ.get("OPENAI_COMPAT_MODEL", "")


def available() -> bool:
    return bool(os.environ.get("OPENAI_COMPAT_BASE_URL") and model())


def setup_hint() -> str:
    return "set OPENAI_COMPAT_BASE_URL, OPENAI_COMPAT_API_KEY and OPENAI_COMPAT_MODEL."


def analyze(image_bytes: bytes, media_type: str, hint: str = "") -> Detection:
    image = base64.standard_b64encode(prepare_image(image_bytes, 1024)).decode()
    # json_object mode is widely supported; strict json_schema is not, so the
    # schema goes in the prompt and the answer is validated below.
    system = (f"{SYSTEM}\n\nReply with a single JSON object matching this JSON schema, "
              f"and nothing else:\n{json.dumps(SCHEMA)}")
    payload = {
        "model": model(),
        "temperature": 0,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": [
                {"type": "text", "text": user_prompt(hint)},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}},
            ]},
        ],
    }
    base = os.environ["OPENAI_COMPAT_BASE_URL"].rstrip("/")
    req = urllib.request.Request(
        f"{base}/chat/completions", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {os.environ.get('OPENAI_COMPAT_API_KEY', 'none')}"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.load(resp)
    except urllib.error.HTTPError as e:
        status = 429 if e.code == 429 else 502
        raise EngineError(f"{LABEL} error ({e.code}): {e.read().decode()[:200]}", status)
    except (urllib.error.URLError, OSError) as e:
        raise EngineError(f"Couldn't reach {LABEL} at {base}: {e}", 503)

    try:
        text = body["choices"][0]["message"]["content"]
        return Detection.model_validate(json.loads(text))
    except (KeyError, IndexError, TypeError, ValueError):
        raise EngineError(f"{LABEL} returned an unreadable answer; try again.", 502)
