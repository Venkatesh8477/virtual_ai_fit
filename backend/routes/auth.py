from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from database import DatabaseManager
from utils.auth import hash_password, verify_password, create_access_token, get_current_user_id

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    email = req.email.strip().lower()
    if "@" not in email:
        email = f"{email}@example.com"
        
    if len(req.password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 4 characters long."
        )

    existing = await DatabaseManager.find_user_by_email(email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Try signing in."
        )
    
    hashed_pwd = hash_password(req.password)
    user = await DatabaseManager.create_user(req.name, email, hashed_pwd)
    
    token = create_access_token({"sub": user["id"], "email": user["email"]})
    
    safe_user = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "createdAt": user.get("createdAt", "")
    }
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": safe_user
    }

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    email = req.email.strip().lower()
    if "@" not in email:
        email = f"{email}@example.com"

    user = await DatabaseManager.find_user_by_email(email)
    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials."
        )
    
    token = create_access_token({"sub": user["id"], "email": user["email"]})
    
    safe_user = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "createdAt": user.get("createdAt", "")
    }
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": safe_user
    }

@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user_id)):
    user = await DatabaseManager.find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "createdAt": user.get("createdAt", "")
    }
