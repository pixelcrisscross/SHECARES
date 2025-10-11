import datetime
import os
import json
from io import BytesIO

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

import pandas as pd
import joblib
import google.generativeai as genai
from PIL import Image

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ CRITICAL: GEMINI_API_KEY not set.")
else:
    print("✅ GEMINI_API_KEY loaded successfully.")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="SheCares AI API",
    description="An integrated API for cycle prediction, pregnancy tools, and AI-powered health assistance.",
    version="3.1.0"
)

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Load Machine Learning Model ---
try:
    period_model_pipeline = joblib.load("period_predictor_model.pkl")
except FileNotFoundError:
    print("⚠️ Warning: 'period_predictor_model.pkl' not found.")
    period_model_pipeline = None

# --- Gemini AI Configuration ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ CRITICAL: GEMINI_API_KEY not set.")
    gemini_model = None
else:
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# --- Request Models ---
class DueDateRequest(BaseModel):
    lmp_date: datetime.date = Field(..., example="2025-01-01")

class AdvancedPeriodRequest(BaseModel):
    last_period_date: datetime.date
    age: int
    bmi: float
    stress_level: int
    sleep_hours: float
    period_length: int
    exercise_freq: str
    diet: str
    symptoms: str

class ChatbotRequest(BaseModel):
    user_input: str = Field(..., min_length=3)

# --- Root Endpoint ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the SheCares AI API"}

# --- Due Date Calculator ---
@app.post("/calculate-due-date")
def calculate_due_date(request: DueDateRequest):
    due_date = request.lmp_date + datetime.timedelta(days=280)
    return {"estimated_due_date": due_date.strftime("%Y-%m-%d")}

# --- Period Prediction (Advanced) ---
@app.post("/predict-ovulation/advanced")
def predict_ovulation_advanced(request: AdvancedPeriodRequest):
    if period_model_pipeline is None:
        raise HTTPException(status_code=503, detail="Machine Learning model unavailable.")

    df_data = {
        'Age': [request.age],
        'BMI': [request.bmi],
        'Stress Level': [request.stress_level],
        'Exercise Frequency': [request.exercise_freq],
        'Sleep Hours': [request.sleep_hours],
        'Diet': [request.diet],
        'Period Length': [request.period_length],
        'Symptoms': [request.symptoms]
    }
    input_df = pd.DataFrame(df_data)

    predicted_cycle_length = int(round(period_model_pipeline.predict(input_df)[0]))
    next_period_date = request.last_period_date + datetime.timedelta(days=predicted_cycle_length)
    ovulation_date = next_period_date - datetime.timedelta(days=14)
    fertile_window_start = ovulation_date - datetime.timedelta(days=5)

    return {
        "predicted_cycle_length_days": predicted_cycle_length,
        "next_period_predicted_date": next_period_date.strftime("%Y-%m-%d"),
        "approximate_ovulation_date": ovulation_date.strftime("%Y-%m-%d"),
        "fertile_window_start": fertile_window_start.strftime("%Y-%m-%d"),
        "fertile_window_end": ovulation_date.strftime("%Y-%m-%d")
    }

# --- Simple Chatbot (Rule-Based) ---
@app.post("/chatbot")
def get_simple_chatbot_response(request: ChatbotRequest):
    responses = {
        "pregnancy": "For a healthy pregnancy, eat a balanced diet, stay hydrated, and walk lightly. Consult your doctor for personalized care.",
        "period": "To reduce cramps, try a hot water bag, gentle yoga, or rest. If pain persists, consult a gynecologist.",
        "mental": "For mental well-being, take deep breaths, journal your thoughts, or meditate for 5–10 minutes daily."
    }
    text = request.user_input.lower()
    for key, reply in responses.items():
        if key in text:
            return {"bot_response": reply}
    return {"bot_response": "I'm here to help! Ask me about pregnancy, periods, or mental health."}

# --- Food Analysis with Gemini ---
@app.post("/analyse-food")
async def analyse_food(file: UploadFile = File(...)):
    if not gemini_model:
        raise HTTPException(status_code=503, detail="Gemini AI not configured.")
    try:
        contents = await file.read()
        print(f"Received file: {file.filename}, size: {len(contents)} bytes")
        image = Image.open(BytesIO(contents))
        print("Image opened successfully.")
        prompt = (
            "Analyse this food image in the context of women's health during pregnancy. "
            "Return JSON: {items:[], safe_to_eat:bool, confidence_score:float, pros:[], cons:[]}"
        )
        response = gemini_model.generate_content([prompt, image])
        print("Gemini response:", response.text)
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except json.JSONDecodeError:
        print("JSON decode error. Raw response:", response.text)
        return {"analysis_text": response.text}
    except Exception as e:
        print("Error in /analyse-food:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# --- Text Chat with Gemini ---
@app.post("/chat/text")
async def chat_text(message: str = Form(...)):
    if not gemini_model:
        raise HTTPException(status_code=503, detail="Gemini AI not configured.")
    try:
        prompt = f"You are an empathetic AI assistant for women's health. User asks: '{message}'"
        response = gemini_model.generate_content(prompt)
        return {"reply": response.text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
