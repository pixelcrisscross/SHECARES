# app_v2.py
import os
import io
import json
import time
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
import mediapipe as mp
import torch
from facenet_pytorch import InceptionResnetV1
from PIL import Image
from torchvision import transforms
from motor.motor_asyncio import AsyncIOMotorClient
from sklearn.neighbors import NearestNeighbors

# ------------ CONFIG ------------

# Replace with your URI (keep it private in production using env vars)
MONGO_URI = "mongodb+srv://omkarputti14_db_user:SrNWlwf8PoWZPGGz@oscorp.d2i0sju.mongodb.net/?retryWrites=true&w=majority&appName=oscorp"

DB_NAME = "face_db"
USERS_COLL = "users"

# similarity threshold (cosine) — tune later
SIMILARITY_THRESHOLD = 0.72

# ------------ APP ------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ------------ MODELS ------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

preprocess = transforms.Compose([
    transforms.Resize((160, 160)),
    transforms.ToTensor(),
    transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
])

mp_face_mesh = mp.solutions.face_mesh
mp_face_mesh_holistic = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

# ------------ MONGO ------------
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]
users_col = db[USERS_COLL]

# ------------ KNN INDEX (in-memory) ------------
_knn = None
_knn_embeddings = None  # numpy array Nx512
_knn_labels = None      # list of user names aligned with embeddings


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


# ------------ UTILITIES ------------
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

    # Landmarks
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


# ------------ ENDPOINTS ------------

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