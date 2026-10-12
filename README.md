# AI Virtual Try-On Studio 👗✨

An end-to-end AI-powered Virtual Try-On web application built with **React**, **Tailwind CSS**, **FastAPI**, **MediaPipe**, **IDM-VTON (Google Colab GPU)**, and **MongoDB**.

---

## 🌟 Features & Modules Overview

### Module 1: Authentication & User Accounts
- User Registration & Login with secure password hashing (`hashlib` / `bcrypt`).
- JSON Web Token (JWT) stateless session authentication.
- User profile tracking.

### Module 2: Image Upload Studio
- Drag-and-drop file uploaders for **Full-body person photo** and **Dress/garment image**.
- Quick 1-click test model presets for instant demonstration.

### Module 3: Body Analysis Engine (MediaPipe Pose)
- Detects 33 anatomical keypoints: Head, Neck, Shoulders, Elbows, Wrists, Chest, Waist, Hips, Knees, and Ankles.
- Real-time estimation of body measurements:
  - **Shoulder width** (cm & px)
  - **Waist width** (cm & px)
  - **Hip width** (cm & px)
  - **Arm length** (cm & px)
  - **Leg length** (cm & px)
  - **Body ratio** (Torso-to-leg proportion)
  - **Body Type Shape Classification** (Hourglass, Inverted Triangle, Rectangle)
- Renders interactive landmark visualization canvas.

### Module 4: Body Segmentation (MediaPipe Selfie Segmentation)
- Foreground person extraction and background removal.
- Returns clean transparent PNG background-removed subject.

### Module 5: Virtual Try-On Pipeline (IDM-VTON & Google Colab)
- Google Colab Jupyter Notebook setup (`colab/VirtualTryOn.ipynb`) for GPU-accelerated IDM-VTON / CatVTON neural rendering with `pyngrok` public tunnel API export.
- FastAPI backend Colab connector with automatic pose-aligned composite fallback mode when Colab GPU is offline.

### Module 6: Result & Inspection Page
- Multi-tab view:
  - **Original Person Photo** & **Selected Dress**
  - **MediaPipe Pose Landmarks Overlay & Keypoint Inspector**
  - **MediaPipe Selfie Background Removed Foreground**
  - **Final AI Try-On Image**
- Instant High-Resolution **Download**, **Save to History**, and **Try Another Dress** actions.

### Module 7: History Gallery & Persistence
- Stores upload dates, person photo, dress image, generated result image, and MediaPipe body proportion metrics.
- MongoDB Atlas driver integration (`motor` / `pymongo`) with built-in embedded JSON fallback.

---

## 📁 Directory Structure

```
AI-Virtual-TryOn/
│
├── frontend/                     # React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── api/client.js         # Axios API service
│   │   ├── components/           # Navbar, ImageUploader, LandmarkCanvas
│   │   ├── context/AuthContext.jsx # Global JWT session provider
│   │   ├── pages/                # Login, Register, Upload, Result, History
│   │   ├── App.jsx               # React Router layout
│   │   └── index.css             # Tailwind v4 glassmorphism design system
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── backend/                      # FastAPI Python Service
│   ├── routes/                   # auth.py, upload.py, tryon.py, history.py
│   ├── mediapipe_engine/         # pose_detector.py & segmentor.py
│   ├── utils/auth.py             # JWT & Password security helpers
│   ├── database.py               # MongoDB Atlas manager + local fallback
│   ├── uploads/                  # Local temporary storage
│   ├── main.py                   # FastAPI server entry point
│   └── requirements.txt          # Python dependencies
│
├── colab/
│   └── VirtualTryOn.ipynb        # Google Colab notebook for IDM-VTON GPU runner
│
└── README.md                     # Documentation
```

---

## 🚀 Quick Start (Local Setup)

### 1. Backend Setup (FastAPI)
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python main.py
```
> FastAPI backend runs on **http://localhost:8000** (Swagger API docs at `http://localhost:8000/docs`).

### 2. Frontend Setup (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
> React frontend runs on **http://localhost:5173**.

---

## ☁️ Deployment Guide

### Frontend Deployment (Vercel)
1. Push `AI-Virtual-TryOn` repository to GitHub.
2. Log into [Vercel](https://vercel.com) and click **Add New Project**.
3. Select the `frontend` folder as the Root Directory.
4. Set Environment Variable: `VITE_API_URL = https://your-backend.onrender.com`.
5. Click **Deploy**.

### Backend Deployment (Render)
1. Log into [Render](https://render.com) and click **New Web Service**.
2. Connect your GitHub repository and set Root Directory to `backend`.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables:
   - `MONGODB_URL = mongodb+srv://<user>:<password>@cluster0.xxx.mongodb.net`
   - `JWT_SECRET = your_jwt_secret_key`

---

## 🤖 Google Colab IDM-VTON GPU Setup
1. Open `colab/VirtualTryOn.ipynb` in [Google Colab](https://colab.research.google.com).
2. Set Runtime type to **T4 GPU**.
3. Run all cells sequentially.
4. Copy the generated `ngrok` public tunnel URL (e.g., `https://xxxx.ngrok-free.app`).
5. Paste the URL into the **Colab GPU** top bar in the web app.
