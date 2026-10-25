# Multi-Language Translator

Translates text between 19 languages (including Swahili, Luganda, Yoruba, Zulu and
Amharic) using [facebook/nllb-200-distilled-600M](https://huggingface.co/facebook/nllb-200-distilled-600M).

```
multi-language-translator/
├── backend/
│   ├── main.py             # FastAPI — /health, /languages, /translate
│   ├── requirements.txt
│   └── .env.example        # CORS_ORIGINS
├── frontend/
│   ├── app.py              # Streamlit UI
│   ├── requirements.txt
│   └── .env.example        # BACKEND_URL
└── tests/                  # pytest
```

## Run

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Windows
pip install -r backend/requirements.txt -r frontend/requirements.txt
uvicorn backend.main:app --port 8000   # first start downloads the model
streamlit run frontend/app.py          # http://localhost:8501
```

## API

| Endpoint | Description |
|---|---|
| `GET /health` | Service and model status |
| `GET /languages` | Supported languages |
| `POST /translate` | `{text, source_language, target_language}` → `{translation}` |

Input is limited to 5,000 characters and is translated in sentence-based chunks.

## Notes

- `truststore` makes Python use the OS certificate store, so Hugging Face downloads
  work behind TLS-inspecting corporate proxies.
- `transformers<5` is pinned because the `translation` pipeline is not available in v5.
