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
- Image-space body estimates from visible MediaPipe landmarks:
  - Shoulder, interpolated waist-line, hip, arm, and leg distances (pixels only)
  - Torso-to-leg ratio and a heuristic silhouette-shape estimate
  - Unusable landmarks are flagged when visibility is low or coordinates fall outside the image
- Pixel distances are not real-world body measurements; centimetre estimates require camera calibration or a known-size reference.
- Renders interactive landmark visualization canvas.

### Module 4: Body Segmentation (MediaPipe Selfie Segmentation)
- Uses the pretrained MediaPipe Selfie Segmentation model to create a soft-alpha RGBA PNG and a grayscale mask preview.
- Reports when the OpenCV GrabCut or center-ellipse fallback was used; segmentation is best-effort and can miss thin limbs or include overlapping background objects.

### Module 5: Virtual Try-On Pipeline (IDM-VTON & Google Colab)
- Google Colab Jupyter Notebook setup (`colab/VirtualTryOn.ipynb`) for GPU-accelerated IDM-VTON / CatVTON neural rendering with `pyngrok` public tunnel API export.
- FastAPI backend Colab connector with automatic pose-aligned composite fallback mode when Colab GPU is offline.
- The local composite uses OpenCV GrabCut with a centered rectangle to extract a tightly cropped transparent garment. It works best when one garment is centered; complex backgrounds can leave attached items such as hangers.

### Module 6: Result & Inspection Page
- Multi-tab view:
  - **Original Person Photo** & **Selected Dress**
  - **MediaPipe Pose Landmarks Overlay & Keypoint Inspector**
  - **MediaPipe Selfie Background Removed Foreground**
  - **Person segmentation mask preview and segmentation method/fallback status**
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

### 1. Backend Setup (Python 3.11 + FastAPI)
From the project root, create and activate the virtual environment and install the backend dependencies:

**Windows (PowerShell):**
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
cd backend
python -m uvicorn main:app --reload
```

**Linux/macOS:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd backend
python -m uvicorn main:app --reload
```
> FastAPI backend runs on **http://localhost:8000** (Swagger API docs at `http://localhost:8000/docs`).

### 2. Frontend Setup (React + Vite)
In a second terminal:
```bash
cd frontend
npm ci
npm run dev
```
> React frontend runs on **http://localhost:5173**.

### 3. Run the component evaluation
From the project root, run:

```powershell
Push-Location backend
..\.venv\Scripts\python.exe -m tests.evaluate
Pop-Location
```

The script evaluates the existing pose photos, reuses them for segmentation, and evaluates the garment photos. Pose categories and person-presence labels come from the visually reviewed `tests/pose-detection/pose_labels.csv` manifest, not filenames; the evaluator rejects missing or extra manifest entries. It appends per-image timings, detection/label agreement, required-landmark coordinates and visibility, mask validity, extraction method, failures, and optional IoU, Dice, precision, and recall to `tests/results/evaluation_results.csv`. Empty-scene segmentation false-foreground pixel counts and fractions are reported separately from mask accuracy. Reference masks must be independently annotated, same-sized PNGs with exact pixel values `0` and `255`; place them under `tests/segmentation/reference_masks/` or `tests/garment-extraction/reference_masks/` using matching image basenames. Only the two verified no-person segmentation references are generated automatically as all-black masks; all positive-person and garment boundaries require human annotation and review. Metrics remain blank until a matching reference exists. Test photos, reference masks, and generated results are ignored by Git.

### Create local reference annotations
Use the OpenCV-based local annotator; it does not upload images or create predictions as labels:

```powershell
.\.venv\Scripts\python.exe tools\annotate_references.py person
.\.venv\Scripts\python.exe tools\annotate_references.py garment
.\.venv\Scripts\python.exe tools\annotate_references.py keypoints
```

For masks, left-click polygon vertices and right-click to close each polygon. Press **B** to switch white/black for islands or holes, **U** to undo, **R** to clear, **S** to save, **N** to skip, and **Q** to quit. The two visually verified empty-scene person masks are safely created as all-black PNGs; the other person masks and all garment masks require drawing and review. Keypoints are clicked in order: nose, subject-left/right shoulder, subject-left/right hip; press **N** when a point is unavailable. Coordinates are source-image pixels in `tests/pose-detection/keypoint_annotations.csv`. Existing annotations are not overwritten. The evaluator calculates PCK@0.2 (normalized by the reference keypoint bounding-box diagonal) only after a complete, valid keypoint CSV is present.

The Phase 3.1 baseline summary, including current results and unmeasured metrics, is documented in [PHASE3_BASELINE.md](./PHASE3_BASELINE.md).

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
