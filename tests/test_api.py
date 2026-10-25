import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from main import MAX_TEXT_CHARS, app, models


@pytest.fixture
def client():
    # Not used as a context manager, so the real model is never loaded.
    calls = []

    def fake_translator(chunks, **kwargs):
        calls.append((chunks, kwargs))
        return [{"translation_text": f"T:{c}"} for c in chunks]

    models["translator"] = fake_translator
    c = TestClient(app)
    c.calls = calls
    yield c
    models.clear()


def _body(**overrides):
    body = {"text": "Hello.", "source_language": "English", "target_language": "French"}
    body.update(overrides)
    return body


def test_health_and_languages(client):
    assert client.get("/health").json()["status"] == "ok"
    assert "Luganda" in client.get("/languages").json()


def test_translate_ok(client):
    r = client.post("/translate", json=_body())
    assert r.status_code == 200
    assert r.json() == {"translation": "T:Hello."}
    assert client.calls[0][1]["src_lang"] == "eng_Latn"
    assert client.calls[0][1]["tgt_lang"] == "fra_Latn"


def test_long_text_is_chunked_and_rejoined(client):
    text = " ".join(["This is a sentence."] * 100)
    r = client.post("/translate", json=_body(text=text))
    assert r.status_code == 200
    assert len(client.calls[0][0]) > 1


def test_unsupported_language(client):
    assert client.post("/translate", json=_body(target_language="Klingon")).status_code == 400


def test_blank_text(client):
    assert client.post("/translate", json=_body(text="   ")).status_code == 400


def test_empty_and_oversized_text(client):
    assert client.post("/translate", json=_body(text="")).status_code == 422
    assert client.post("/translate", json=_body(text="a" * (MAX_TEXT_CHARS + 1))).status_code == 422


def test_same_language_returns_input_without_model_call(client):
    r = client.post("/translate", json=_body(target_language="English"))
    assert r.json() == {"translation": "Hello."}
    assert client.calls == []
