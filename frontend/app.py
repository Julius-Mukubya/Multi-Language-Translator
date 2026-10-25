import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Multi-Language Translator", page_icon="🌍")
st.title("🌍 Multi-Language Translator")


@st.cache_data(ttl=300)
def get_languages():
    resp = requests.get(f"{BACKEND_URL}/languages", timeout=10)
    resp.raise_for_status()
    return list(resp.json().keys())


try:
    languages = get_languages()
except requests.RequestException:
    st.error(f"Cannot reach the backend at {BACKEND_URL}. Is it running?")
    st.stop()

col1, col2 = st.columns(2)
source = col1.selectbox("From", languages, index=languages.index("English"))
target = col2.selectbox("To", languages, index=languages.index("French"))

text = st.text_area("Text to translate", height=150)

if st.button("Translate", type="primary"):
    if not text.strip():
        st.warning("Please enter some text.")
    else:
        with st.spinner("Translating..."):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/translate",
                    json={
                        "text": text,
                        "source_language": source,
                        "target_language": target,
                    },
                    timeout=120,
                )
                resp.raise_for_status()
                st.subheader("Translation")
                st.success(resp.json()["translation"])
            except requests.RequestException as e:
                st.error(f"Translation failed: {e}")
