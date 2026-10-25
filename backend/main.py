from contextlib import asynccontextmanager

import truststore

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import pipeline

# Use the OS certificate store so downloads work behind TLS-inspecting proxies.
truststore.inject_into_ssl()

MODEL_NAME = "facebook/nllb-200-distilled-600M"

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


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1)
    source_language: str
    target_language: str


class TranslateResponse(BaseModel):
    translation: str


@app.get("/languages")
def languages():
    return LANGUAGES


@app.post("/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    if req.source_language not in LANGUAGES or req.target_language not in LANGUAGES:
        raise HTTPException(status_code=400, detail="Unsupported language")
    result = models["translator"](
        req.text,
        src_lang=LANGUAGES[req.source_language],
        tgt_lang=LANGUAGES[req.target_language],
        max_length=512,
    )
    return TranslateResponse(translation=result[0]["translation_text"])
