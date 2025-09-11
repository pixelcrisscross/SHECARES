# 💖 SheCares – Your AI Health Companion

SheCares is an AI-powered health and wellness platform that provides **intelligent health tracking** and **real-time AI assistance**. Designed to be a comprehensive companion, SheCares enables users to monitor their health, gain AI-driven insights, and access safety features interactively — all from the comfort of their browser.

---

## 🚀 Features

- 🤖 **AI-Powered Health Assistant** – Engage in empathetic conversations about your health via text or voice, and get instant nutritional analysis of food from a photo, all powered by Google Gemini.
- 🩸 **Intelligent Cycle Prediction** – Utilizes a custom machine learning model to provide accurate, personalized predictions for menstrual cycles and ovulation windows.
- 🆘 **Emergency SOS System** – A one-click safety feature that instantly retrieves the user's current geolocation, ready to be shared with emergency contacts.
- 🤰 **Comprehensive Pregnancy Tools** – Includes a simple and effective due date calculator to track pregnancy milestones.

---
## 🛆 Tech Stack
 - **Frontend:** React, TypeScript, Vite, Tailwind CSS
 - **Backend:** Python, FastAPI
 - **AI / ML:** Google Gemini, Scikit-learn, gTTS, SpeechRecognition
 - **Deployment:** Vercel

---

## 🛠️ Installation & Setup

### Prerequisites
- Node.js and npm
- Python 3.9+ and pip
- A `.env` file with your `GEMINI_API_KEY`

### 1. Clone the Repo

```bash
git clone https://github.com/pixelcrisscross/SheCares-Oscorp-.git
cd SheCares-Oscorp
```
### 2. Install Dependencies
### 2a. Backend Setup (Python)

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2b. Frontend Setup 

```bash
npm install
```

### 3. Configure Environment
Create a .env.local file and add:
```
GEMINI_API_KEY="your_gemini_api_key_here"
```

### 4. Run 
```bash
npm run dev
```
