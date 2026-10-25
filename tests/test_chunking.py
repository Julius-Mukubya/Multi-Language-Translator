import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from main import chunk_text


def test_short_text_is_one_chunk():
    assert chunk_text("Hello there. How are you?", 800) == ["Hello there. How are you?"]


def test_splits_on_sentence_boundaries():
    chunks = chunk_text("One two. Three four. Five six.", 15)
    assert chunks == ["One two.", "Three four.", "Five six."]
    assert all(len(c) <= 15 for c in chunks)


def test_long_sentence_is_hard_split():
    chunks = chunk_text("a" * 25, 10)
    assert chunks == ["a" * 10, "a" * 10, "a" * 5]


def test_splits_on_amharic_and_arabic_markers():
    assert chunk_text("ሰላም። እንዴት ነህ።", 10) == ["ሰላም።", "እንዴት ነህ።"]
    assert chunk_text("كيف حالك؟ أنا بخير.", 12) == ["كيف حالك؟", "أنا بخير."]
