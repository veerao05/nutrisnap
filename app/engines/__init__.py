"""Pluggable vision engines.

Every engine module exposes the same interface:

    NAME, LABEL, FREE        identifiers shown in the UI
    model() -> str           the model it will call
    available() -> bool      configured and reachable
    setup_hint() -> str      what to do if it isn't available
    analyze(image_bytes, media_type, hint) -> Detection
                             raises EngineError on failure

To add a provider, write a module with that interface and list it in ENGINES.
"""

import os

from . import claude, gemini, ollama, openai_compat
from .base import EngineError


# Order = auto-selection priority when no engine is requested.
ENGINES = {m.NAME: m for m in (claude, gemini, openai_compat, ollama)}


def describe() -> list[dict]:
    return [{
        "name": m.NAME,
        "label": m.LABEL,
        "model": m.model(),
        "free": m.FREE,
        "available": m.available(),
        "setup": m.setup_hint(),
    } for m in ENGINES.values()]


def choose(requested: str | None = None):
    """Engine to use: the requested one, else NUTRISNAP_VISION, else first available."""
    for name in (requested, os.environ.get("NUTRISNAP_VISION")):
        name = (name or "").strip().lower()
        if not name:
            continue
        engine = ENGINES.get(name)
        if engine is None:
            raise EngineError(f"Unknown engine '{name}'. Options: {', '.join(ENGINES)}.", 400)
        if not engine.available():
            raise EngineError(f"{engine.LABEL} isn't available: {engine.setup_hint()}", 503)
        return engine
    for engine in ENGINES.values():
        if engine.available():
            return engine
    raise EngineError("No analysis engine is set up. " + " Or: ".join(
        f"{m.LABEL}: {m.setup_hint()}" for m in ENGINES.values()), 503)


def default_name() -> str | None:
    try:
        return choose().NAME
    except EngineError:
        return None
