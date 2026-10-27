"""API tests with a fake vision engine: no keys, no network, no models.

Run:  .venv/bin/python -m pytest -q
"""

import io
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import engines, storage
from app.detection import DetectedItem, Detection
from app.engines import openai_compat
from app.nutrition_db import resolve_key
from app.tracker import guidance


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), "orange").save(buf, "PNG")
    return buf.getvalue()


class FakeEngine:
    NAME, LABEL, FREE = "fake", "Fake", True
    result = Detection(is_food=True, notes="", items=[
        DetectedItem(name="dal_tadka", db_key=None, grams=150, confidence=0.9,
                     est_kcal_per_100g=0, est_protein_per_100g=0,
                     est_carbs_per_100g=0, est_fat_per_100g=0),
        DetectedItem(name="Mystery stew", db_key=None, grams=200, confidence=0.5,
                     est_kcal_per_100g=100, est_protein_per_100g=5,
                     est_carbs_per_100g=10, est_fat_per_100g=4),
    ])

    @staticmethod
    def model(): return "fake-1"
    @staticmethod
    def available(): return True
    @staticmethod
    def setup_hint(): return "nothing"
    @classmethod
    def analyze(cls, image_bytes, media_type, hint=""): return cls.result


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.init()
    monkeypatch.setattr(engines, "ENGINES", {"fake": FakeEngine})
    monkeypatch.delenv("NUTRISNAP_VISION", raising=False)
    from app.main import app
    return TestClient(app)


def analyze(client, **form):
    return client.post("/api/analyze", files={"image": ("m.png", _png(), "image/png")},
                       data=form)


def test_analyze_uses_db_and_falls_back_to_estimate(client):
    r = analyze(client)
    assert r.status_code == 200
    items = {i["name"]: i for i in r.json()["items"]}
    assert items["Dal tadka"]["source"] == "database"      # key matched by name
    assert items["Dal tadka"]["calories"] == round(116 * 1.5)
    assert items["Mystery stew"]["source"] == "model estimate"
    assert items["Mystery stew"]["calories"] == 200
    assert r.json()["engine"]["name"] == "fake"


def test_no_food_is_rejected(client, monkeypatch):
    monkeypatch.setattr(FakeEngine, "result", Detection(is_food=False, items=[], notes=""))
    assert analyze(client).status_code == 422


def test_unknown_and_unavailable_engines(client, monkeypatch):
    assert analyze(client, engine="nope").status_code == 400
    monkeypatch.setattr(FakeEngine, "available", staticmethod(lambda: False))
    r = analyze(client)
    assert r.status_code == 503 and "No analysis engine" in r.json()["detail"]


def test_rejects_non_images(client):
    r = client.post("/api/analyze", files={"image": ("a.txt", b"hi", "text/plain")})
    assert r.status_code == 415


def test_log_and_delete_meal_updates_totals(client):
    items = analyze(client).json()["items"]
    day = client.post("/api/meals", json={"label": "Lunch", "items": items}).json()
    assert day["consumed"]["calories"] == 174 + 200
    day = client.delete(f"/api/meals/{day['meals'][0]['id']}").json()
    assert day["consumed"]["calories"] == 0


def test_goal_must_sum_to_100(client):
    bad = {"calories": 2000, "protein_pct": 50, "carbs_pct": 40, "fat_pct": 30}
    assert client.put("/api/goal", json=bad).status_code == 400
    ok = {**bad, "protein_pct": 30}
    assert client.put("/api/goal", json=ok).json()["target"]["protein"] == 150


def test_engines_endpoint(client):
    body = client.get("/api/engines").json()
    assert body["default"] == "fake" and body["engines"][0]["model"] == "fake-1"


def test_resolve_key():
    assert resolve_key(None, "White rice, cooked") == "white_rice_cooked"
    assert resolve_key("bogus", "chickpeas_cooked") == "chickpeas_cooked"
    assert resolve_key(None, "mystery stew") is None


def test_guidance_messages():
    target = {"calories": 2000, "protein": 150, "carbs": 200, "fat": 67}
    eaten = {"calories": 2400, "protein": 100, "carbs": 260, "fat": 90}
    assert guidance(eaten, target)["status"] == "over"
    zero = {k: 0 for k in target}
    assert guidance(zero, target)["status"] == "empty"


def test_openai_compatible_engine_against_fake_server(monkeypatch):
    """Exercises the real request/parse code against a local stand-in server."""
    seen = {}
    answer = {"is_food": True, "notes": "", "items": [{
        "name": "Idli", "db_key": "idli", "grams": 120, "confidence": 0.9,
        "est_kcal_per_100g": 135, "est_protein_per_100g": 4,
        "est_carbs_per_100g": 28, "est_fat_per_100g": 0.5}]}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen["path"] = self.path
            seen["auth"] = self.headers["Authorization"]
            seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            out = json.dumps({"choices": [{"message": {"content": json.dumps(answer)}}]})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(out.encode())

        def log_message(self, *a): pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
    monkeypatch.setenv("OPENAI_COMPAT_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_COMPAT_MODEL", "some-vision-model")
    try:
        result = openai_compat.analyze(_png(), "image/png")
    finally:
        server.shutdown()

    assert result.items[0].db_key == "idli"
    assert seen["path"] == "/v1/chat/completions"
    assert seen["auth"] == "Bearer test-key"
    content = seen["body"]["messages"][1]["content"]
    assert content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
