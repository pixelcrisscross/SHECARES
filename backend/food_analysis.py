import os
import re
import time
import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# --- Load environment variables ---
load_dotenv()

router = APIRouter(prefix="/gemini", tags=["Gemini Food AI"])

# --- API Key ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("⚠️ GEMINI_API_KEY missing in .env file.")

# --- Configure Gemini SDK ---
genai.configure(api_key=GEMINI_API_KEY)

# --- Caching ---
_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SEC = 60 * 30  # 30 min

def cache_result(key: str, value: Dict[str, Any]):
    _cache[key] = {"ts": time.time(), "value": value}

def get_cached(key: str):
    v = _cache.get(key)
    if not v:
        return None
    if time.time() - v["ts"] > CACHE_TTL_SEC:
        del _cache[key]
        return None
    return v["value"]

# --- Input/Output Models ---
class SuggestRequest(BaseModel):
    medicineName: str

class SuggestResponse(BaseModel):
    before: list[str]
    after: list[str]

# --- Helper Functions ---
def sanitize_input(s: str) -> str:
    s = str(s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s[:120]

def extract_json_object(text: str):
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None

# --- API Route ---
@router.post("/food-suggestions", response_model=SuggestResponse)
async def food_suggestions(req: SuggestRequest):
    name_raw = req.medicineName
    if not isinstance(name_raw, str) or not name_raw.strip():
        raise HTTPException(status_code=400, detail="medicineName is required.")

    name = sanitize_input(name_raw)
    cache_key = f"food:{name.lower()}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    prompt = (
        f"You are a medical nutrition expert. Based on the medicine below, return a JSON object:\n"
        f"{{ \"before\": [...], \"after\": [...] }}\n"
        f"Each array must include 3–6 short food names (1–4 words) that are safe to eat "
        f"BEFORE or AFTER taking the medicine for better absorption or reduced side effects.\n"
        f"Return ONLY JSON, no text outside JSON.\n\n"
        f'Medicine: "{name}"'
    )

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw_text = response.text.strip() if response.text else ""
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini request failed: {str(e)}")

    parsed = extract_json_object(raw_text)
    if parsed is None:
        parsed = {"before": [], "after": []}

    before = [str(x).strip() for x in parsed.get("before", [])][:12]
    after = [str(x).strip() for x in parsed.get("after", [])][:12]
    result = {"before": before, "after": after}
    cache_result(cache_key, result)

    return result

# --- Health Check ---
@router.get("/ping")
async def ping():
    return {"ok": True}
