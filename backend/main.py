import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes.auth import router as auth_router
from routes.upload import router as upload_router
from routes.tryon import router as tryon_router
from routes.history import router as history_router

app = FastAPI(
    title="AI Virtual Try-On API",
    description="Backend service powered by FastAPI, MediaPipe Pose & Selfie Segmentation, IDM-VTON Google Colab pipeline, and MongoDB.",
    version="1.0.0"
)

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploads directory static serving
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Mount Routers
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(tryon_router)
app.include_router(history_router)

@app.get("/")
async def root():
    return {
        "app": "AI Virtual Try-On API",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
