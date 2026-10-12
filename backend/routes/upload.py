import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from utils.auth import get_current_user_id

router = APIRouter(prefix="/api/upload", tags=["Upload"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are permitted.")
    
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
        
    return {
        "filename": filename,
        "url": f"/uploads/{filename}",
        "size": len(content)
    }
