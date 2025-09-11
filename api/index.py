import datetime
import os
import json
import tempfile
from io import BytesIO
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import pandas as pd
import joblib
import numpy as np
import cv2
import mediapipe as mp
import torch
from facenet_pytorch import InceptionResnetV1
from torchvision import transforms
from sklearn.neighbors import NearestNeighbors
import google.generativeai as genai
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from PIL import Image
import speech_recognition as sr
from gtts import gTTS

load_dotenv()

app = FastAPI(
    title="SheCares AI API",
    description="An integrated API for cycle prediction, pregnancy tools, and AI-powered health assistance.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],    
)

try:
    period_model_pipeline = joblib.load("period_predictor_model.pkl")
except FileNotFoundError:
    print("Warning: period_predictor_model.pkl not found. Advanced prediction endpoints will fail.")
    period_model_pipeline = None

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("CRITICAL: GEMINI_API_KEY environment variable not set. Gemini endpoints will fail.")
    gemini_model = None
else:
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set!")

DB_NAME = "face_db"
USERS_COLL = "users"
SIMILARITY_THRESHOLD = 0.72

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

preprocess = transforms.Compose([
    transforms.Resize((160, 160)),
    transforms.ToTensor(),
    transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
])

mp_face_mesh_holistic = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]
users_col = db[USERS_COLL]

_knn = None
_knn_embeddings = None
_knn_labels = None

def rebuild_knn_index(embeddings_per_user: dict, n_neighbors=5):
    global _knn, _knn_embeddings, _knn_labels
    all_embs, labels = [], []
    for name, embs in embeddings_per_user.items():
        for e in embs:
            all_embs.append(e)
            labels.append(name)
    if len(all_embs) == 0:
        _knn = _knn_embeddings = _knn_labels = None
        return
    arr = np.vstack(all_embs)
    neigh = NearestNeighbors(
        n_neighbors=min(n_neighbors, len(arr)),
        metric='cosine',
        algorithm='auto'
    )
    neigh.fit(arr)
    _knn = neigh
    _knn_embeddings = arr
    _knn_labels = labels

def read_imagefile_bytes(file_bytes: bytes):
    npimg = np.frombuffer(file_bytes, np.uint8)
    return cv2.imdecode(npimg, cv2.IMREAD_COLOR)


def align_and_crop_face_bgr(image_bgr):
    img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    results = mp_face_mesh_holistic.process(img_rgb)
    if not results.multi_face_landmarks:
        return None
    lm = results.multi_face_landmarks[0].landmark
    h, w, _ = image_bgr.shape

    idx_left_eye, idx_right_eye, idx_nose = 33, 263, 1
    left = lm[idx_left_eye]
    right = lm[idx_right_eye]
    nose = lm[idx_nose]

    left_pt = np.array([left.x * w, left.y * h])
    right_pt = np.array([right.x * w, right.y * h])
    nose_pt = np.array([nose.x * w, nose.y * h])

    eyes_center = (left_pt + right_pt) / 2.0
    dy, dx = right_pt[1] - left_pt[1], right_pt[0] - left_pt[0]
    angle = np.degrees(np.arctan2(dy, dx))

    eye_dist = np.linalg.norm(right_pt - left_pt)
    desired_w, desired_h = int(eye_dist * 4.0), int(eye_dist * 4.8)

    M = cv2.getRotationMatrix2D(tuple(eyes_center), angle, 1.0)
    rotated = cv2.warpAffine(image_bgr, M, (w, h), flags=cv2.INTER_CUBIC)

    nose_pt_rot = np.dot(M, np.array([nose_pt[0], nose_pt[1], 1.0]))
    x_c, y_c = int(nose_pt_rot[0]), int(nose_pt_rot[1])

    x1, x2 = max(0, x_c - desired_w // 2), min(w, x_c + desired_w // 2)
    y1, y2 = max(0, y_c - desired_h // 2), min(h, y_c + desired_h // 2)

    crop = rotated[y1:y2, x1:x2]
    return crop if crop.size > 0 else None


def get_embedding_from_bgr_aligned(bgr_img):
    crop = align_and_crop_face_bgr(bgr_img)
    if crop is None:
        return None
    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    tensor = preprocess(pil).unsqueeze(0).to(device)
    with torch.no_grad():
        emb = resnet(tensor).cpu().numpy()[0]
    return (emb / np.linalg.norm(emb)).astype(float)


async def load_all_embeddings_from_db():
    cursor = users_col.find({})
    out = {}
    async for doc in cursor:
        name = doc.get("name")
        embs = doc.get("embeddings", [])
        out[name] = [np.array(e, dtype=float) for e in embs]
    return out

class DueDateRequest(BaseModel):
    lmp_date: datetime.date = Field(..., example="2025-01-01")

class SimplePeriodRequest(BaseModel):
    last_period_date: datetime.date = Field(..., example="2025-08-15")
    cycle_length: int = Field(28, gt=19, lt=46)

class AdvancedPeriodRequest(BaseModel):
    last_period_date: datetime.date
    age: int; bmi: float; stress_level: int; sleep_hours: float; period_length: int
    exercise_freq: str; diet: str; symptoms: str

class ChatbotRequest(BaseModel):
    user_input: str = Field(..., min_length=3)

@app.on_event("startup")
async def startup_event():
    embs = await load_all_embeddings_from_db()
    rebuild_knn_index(embs)

@app.get("/users")
async def list_users():
    docs = []
    cursor = users_col.find({}, {"name": 1, "created_at": 1, "updated_at": 1, "count": 1})
    async for d in cursor:
        docs.append({"name": d.get("name"), "count": d.get("count", 0)})
    return {"users": docs}


@app.post("/enroll")
async def enroll(name: str = Form(...), file: UploadFile = File(...)):
    contents = await file.read()
    img = read_imagefile_bytes(contents)
    emb = get_embedding_from_bgr_aligned(img)
    if emb is None:
        return {"success": False, "reason": "no_face_detected"}
    now = datetime.utcnow().isoformat()
    existing = await users_col.find_one({"name": name})
    if existing:
        await users_col.update_one(
            {"_id": existing["_id"]},
            {"$push": {"embeddings": emb.tolist()},
             "$set": {"updated_at": now},
             "$inc": {"count": 1}}
        )
    else:
        doc = {"name": name, "embeddings": [emb.tolist()],
               "created_at": now, "updated_at": now, "count": 1}
        await users_col.insert_one(doc)
    embs = await load_all_embeddings_from_db()
    rebuild_knn_index(embs)
    return {"success": True, "name": name}


@app.post("/verify")
async def verify(file: UploadFile = File(...), name: Optional[str] = Form(None)):
    contents = await file.read()
    img = read_imagefile_bytes(contents)
    emb = get_embedding_from_bgr_aligned(img)
    if emb is None:
        return {"success": False, "reason": "no_face_detected"}
    if name:
        doc = await users_col.find_one({"name": name})
        if not doc:
            return {"success": False, "reason": "user_not_found"}
        scores = [float(np.dot(emb, np.array(e))) for e in doc.get("embeddings", [])]
        best = max(scores) if scores else -1.0
        return {"success": True, "claimed": name, "score": best, "is_match": best >= SIMILARITY_THRESHOLD}
    if _knn is not None:
        dist, idxs = _knn.kneighbors(emb.reshape(1, -1), n_neighbors=1, return_distance=True)
        sim = 1.0 - float(dist[0][0])
        label = _knn_labels[idxs[0][0]] if _knn_labels else None
        return {"success": True, "best_match": label, "score": sim, "is_match": sim >= SIMILARITY_THRESHOLD}
    return {"success": False, "reason": "index_not_ready"}

@app.get("/")
def read_root():
    return {"message": "Welcome to the SheCares AI API"}

@app.post("/calculate-due-date")
def calculate_due_date(request: DueDateRequest):
    due_date = request.lmp_date + datetime.timedelta(days=280)
    return {"estimated_due_date": due_date.strftime("%Y-%m-%d")}

@app.post("/predict-ovulation/advanced")
def predict_ovulation_advanced(request: AdvancedPeriodRequest):
    if period_model_pipeline is None:
        raise HTTPException(status_code=503, detail="Machine Learning model is not available.")
    
    df_data = { 'Age': [request.age], 'BMI': [request.bmi], 'Stress Level': [request.stress_level], 'Exercise Frequency': [request.exercise_freq], 'Sleep Hours': [request.sleep_hours], 'Diet': [request.diet], 'Period Length': [request.period_length], 'Symptoms': [request.symptoms] }
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

@app.post("/chatbot")
def get_simple_chatbot_response(request: ChatbotRequest):
    """Provides a simple, rule-based response for common questions."""
    responses = { "pregnancy": "For a healthy pregnancy, focus on a balanced diet rich in iron and folate, stay hydrated, and engage in light exercise like walking. Always consult your doctor for personalized advice.", "period": "To alleviate period cramps, you can try using a hot water bag, doing gentle yoga stretches, or some mild exercise. If pain is severe, please see a doctor.", "mental": "For mental well-being, practicing mindfulness can be helpful. Take a few deep breaths, consider journaling your thoughts, or try a guided meditation for 5-10 minutes." }
    user_input_lower = request.user_input.lower()
    for keyword, response in responses.items():
        if keyword in user_input_lower:
            return {"bot_response": response}
    return {"bot_response": "I'm here to help! Please ask a question about pregnancy, periods, or mental health."}

@app.post("/analyse-food")
async def analyse_food(file: UploadFile = File(...)):
    if not gemini_model: raise HTTPException(status_code=503, detail="Gemini AI model is not configured.")
    try:
        contents = await file.read()
        image = Image.open(BytesIO(contents))
        prompt = ( "Analyse this food image in the context of women's health with respect pregnancy as a context!" "Return a clean JSON object (no markdown) with fields: " "'items' (list of strings), 'safe_to_eat' (boolean), " "'confidence_score' (float 0-1), 'pros' (list of strings), 'cons' (list of strings)." )
        response = gemini_model.generate_content([prompt, image])
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except json.JSONDecodeError: return {"analysis_text": response.text}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/text")
async def chat_text(message: str = Form(...)):
    if not gemini_model: raise HTTPException(status_code=503, detail="Gemini AI model is not configured.")
    try:
        contextual_message = f"You are a helpful, empathetic AI assistant for women's health. A user asks: '{message}'"
        response = gemini_model.generate_content(contextual_message)
        return {"reply": response.text}
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/chat/voice")
async def chat_voice(file: UploadFile = File(...), return_audio: bool = Form(False)):
    if not gemini_model: raise HTTPException(status_code=503, detail="Gemini AI model is not configured.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_in:
        contents = await file.read(); temp_audio_in.write(contents); audio_in_path = temp_audio_in.name
    try:
        recognizer = sr.Recognizer();
        with sr.AudioFile(audio_in_path) as source: audio_data = recognizer.record(source); user_text = recognizer.recognize_google(audio_data)
        contextual_message = f"You are a helpful AI assistant for women's health. User asks: '{user_text}'"; gemini_response = gemini_model.generate_content(contextual_message).text
        if not return_audio: return {"user_text": user_text, "reply": gemini_response}
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_out:
            tts = gTTS(text=gemini_response, lang='en'); tts.save(temp_audio_out.name)
            return FileResponse(temp_audio_out.name, media_type="audio/mpeg", filename="response.mp3")
    except sr.UnknownValueError: raise HTTPException(status_code=400, detail="Could not understand the audio.")
    except sr.RequestError as e: raise HTTPException(status_code=503, detail=f"Speech recognition service error: {e}")
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(audio_in_path): os.remove(audio_in_path)