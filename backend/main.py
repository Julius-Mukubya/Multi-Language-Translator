import os
import re
from contextlib import asynccontextmanager
from typing import List

import truststore

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import pipeline

# Use the OS certificate store so downloads work behind TLS-inspecting proxies.
truststore.inject_into_ssl()

MODEL_NAME = "facebook/nllb-200-distilled-600M"

# Reject oversized inputs, and split what is accepted into sentence-based chunks
# so each model call stays well inside NLLB's 512-token limit.
MAX_TEXT_CHARS = 5_000
CHUNK_SIZE = 800

# NLLB-200 language codes for a common subset of supported languages.
LANGUAGES = {
    "English": "eng_Latn",
    "French": "fra_Latn",
    "Spanish": "spa_Latn",
    "German": "deu_Latn",
    "Italian": "ita_Latn",
    "Portuguese": "por_Latn",
    "Dutch": "nld_Latn",
    "Russian": "rus_Cyrl",
    "Arabic": "arb_Arab",
    "Hindi": "hin_Deva",
    "Chinese (Simplified)": "zho_Hans",
    "Japanese": "jpn_Jpan",
    "Korean": "kor_Hang",
    "Turkish": "tur_Latn",
    "Swahili": "swh_Latn",
    "Luganda": "lug_Latn",
    "Yoruba": "yor_Latn",
    "Zulu": "zul_Latn",
    "Amharic": "amh_Ethi",
}

models = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    models["translator"] = pipeline("translation", model=MODEL_NAME)
    yield
    models.clear()


app = FastAPI(title="Multi-Language Translator", lifespan=lifespan)

_raw_origins = os.environ.get("CORS_ORIGINS", "http://localhost:8501")
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """Split *text* into chunks of at most *chunk_size* characters on sentence boundaries."""
    sentences = re.split(r"(?<=[.!?。！？።؟])\s+", text.strip())
    chunks: List[str] = []
    current = ""
    for sentence in sentences:
        # A single over-long sentence is hard-split so it still fits.
        while len(sentence) > chunk_size:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(sentence[:chunk_size])
            sentence = sentence[chunk_size:]
        if current and len(current) + 1 + len(sentence) > chunk_size:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT_CHARS)
    source_language: str
    target_language: str


class TranslateResponse(BaseModel):
    translation: str


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.get("/languages")
def languages():
    return LANGUAGES


@app.post("/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    if req.source_language not in LANGUAGES or req.target_language not in LANGUAGES:
        raise HTTPException(status_code=400, detail="Unsupported language")
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text must not be blank")
    if req.source_language == req.target_language:
        return TranslateResponse(translation=req.text)
    result = models["translator"](
        chunk_text(req.text),
        src_lang=LANGUAGES[req.source_language],
        tgt_lang=LANGUAGES[req.target_language],
        max_length=512,
    )
    return TranslateResponse(translation=" ".join(r["translation_text"] for r in result))
