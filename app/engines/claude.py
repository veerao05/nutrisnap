"""Claude vision (Anthropic API). Paid per photo; the most accurate engine.

Setup: export ANTHROPIC_API_KEY=sk-ant-...   (from console.anthropic.com)
Model: NUTRISNAP_CLAUDE_MODEL (default claude-opus-5-5; claude-sonnet-5-5 is cheaper)
"""

import base64
import json
import os

import anthropic

from ..detection import SCHEMA, SYSTEM, Detection, prepare_image, user_prompt
from .base import EngineError

NAME = "claude"
LABEL = "Claude"
FREE = False

_client: anthropic.Anthropic | None = None


def model() -> str:
    return os.environ.get("NUTRISNAP_CLAUDE_MODEL",
                          os.environ.get("NUTRISNAP_MODEL", "claude-opus-5-5"))


def available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def setup_hint() -> str:
    return "set ANTHROPIC_API_KEY (console.anthropic.com) and restart the server."


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def analyze(image_bytes: bytes, media_type: str, hint: str = "") -> Detection:
    image = prepare_image(image_bytes, 1568)  # Claude's recommended max edge
    try:
        response = _get_client().beta.messages.create(
            model=model(),
            max_tokens=16000,
            system=SYSTEM,
            output_config={
                "effort": "medium",
                "format": {"type": "json_schema", "schema": SCHEMA},
            },
            # Re-route to a fallback model if a safety classifier declines.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64.standard_b64encode(image).decode(),
                        },
                    },
                    {"type": "text", "text": user_prompt(hint)},
                ],
            }],
        )
    except anthropic.AuthenticationError:
        raise EngineError("Claude rejected the API key; check ANTHROPIC_API_KEY.", 502)
    except anthropic.RateLimitError:
        raise EngineError("Claude rate limit reached; try again shortly.", 429)
    except anthropic.APIStatusError as e:
        raise EngineError(f"Claude API error ({e.status_code}): {e.message}", 502)
    except anthropic.APIConnectionError:
        raise EngineError("Couldn't reach the Claude API.", 503)

    if response.stop_reason == "refusal":
        raise EngineError("Claude declined to analyze this image.", 422)
    if response.stop_reason == "max_tokens":
        raise EngineError("Analysis was cut off; try again.", 502)

    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        return Detection.model_validate(json.loads(text))
    except ValueError:
        raise EngineError("Claude returned an unreadable answer; try again.", 502)
