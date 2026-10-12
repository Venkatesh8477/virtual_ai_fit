import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "")
DB_NAME = os.getenv("DB_NAME", "virtual_tryon_db")

# In-memory storage for fallback mode
_in_memory_users: Dict[str, dict] = {}
_in_memory_history: List[dict] = []
LOCAL_DB_FILE = os.path.join(os.path.dirname(__file__), "local_db_backup.json")

def load_local_db():
    global _in_memory_users, _in_memory_history
    if os.path.exists(LOCAL_DB_FILE):
        try:
            with open(LOCAL_DB_FILE, "r") as f:
                data = json.load(f)
                _in_memory_users = data.get("users", {})
                _in_memory_history = data.get("history", [])
        except Exception as e:
            print(f"[Database] Warning reading local fallback DB: {e}")

def save_local_db():
    try:
        with open(LOCAL_DB_FILE, "w") as f:
            json.dump({
                "users": _in_memory_users,
                "history": _in_memory_history
            }, f, indent=2)
    except Exception as e:
        print(f"[Database] Warning saving local fallback DB: {e}")

load_local_db()

# MongoDB Client Setup
db_client = None
db_instance = None
using_mongodb = False

if MONGODB_URL:
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        db_client = AsyncIOMotorClient(MONGODB_URL)
        db_instance = db_client[DB_NAME]
        using_mongodb = True
        print("[Database] Connected to MongoDB Atlas successfully.")
    except Exception as e:
        print(f"[Database] Failed to connect to MongoDB Atlas ({e}). Using local embedded storage.")

class DatabaseManager:
    @staticmethod
    async def find_user_by_email(email: str) -> Optional[dict]:
        email = email.lower().strip()
        if using_mongodb and db_instance is not None:
            try:
                user = await db_instance.users.find_one({"email": email})
                if user:
                    user["id"] = str(user.get("_id", user.get("id")))
                    return user
            except Exception as e:
                print(f"[Database] Mongo find_user error: {e}")
        
        # Fallback
        for u in _in_memory_users.values():
            if u.get("email", "").lower() == email:
                return u
        return None

    @staticmethod
    async def find_user_by_id(user_id: str) -> Optional[dict]:
        if using_mongodb and db_instance is not None:
            try:
                from bson import ObjectId
                user = await db_instance.users.find_one({"_id": ObjectId(user_id)})
                if not user:
                    user = await db_instance.users.find_one({"id": user_id})
                if user:
                    user["id"] = str(user.get("_id", user.get("id")))
                    return user
            except Exception as e:
                print(f"[Database] Mongo find_by_id error: {e}")

        # Fallback
        return _in_memory_users.get(user_id)

    @staticmethod
    async def create_user(name: str, email: str, password_hash: str) -> dict:
        email = email.lower().strip()
        user_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        user_doc = {
            "id": user_id,
            "name": name,
            "email": email,
            "password": password_hash,
            "createdAt": created_at
        }
        
        if using_mongodb and db_instance is not None:
            try:
                res = await db_instance.users.insert_one(user_doc)
                user_doc["id"] = str(res.inserted_id)
                return user_doc
            except Exception as e:
                print(f"[Database] Mongo create_user error: {e}")
        
        # Fallback
        _in_memory_users[user_id] = user_doc
        save_local_db()
        return user_doc

    @staticmethod
    async def save_tryon_history(
        user_id: str,
        person_image: str,
        dress_image: str,
        result_image: str,
        body_analysis: dict,
        segmented_image: Optional[str] = None
    ) -> dict:
        item_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        history_doc = {
            "id": item_id,
            "userId": user_id,
            "personImage": person_image,
            "dressImage": dress_image,
            "resultImage": result_image,
            "segmentedImage": segmented_image or "",
            "bodyAnalysis": body_analysis,
            "createdAt": created_at
        }
        
        if using_mongodb and db_instance is not None:
            try:
                res = await db_instance.TryOnHistory.insert_one(history_doc)
                history_doc["id"] = str(res.inserted_id)
                return history_doc
            except Exception as e:
                print(f"[Database] Mongo save_tryon error: {e}")
        
        # Fallback
        _in_memory_history.insert(0, history_doc)
        save_local_db()
        return history_doc

    @staticmethod
    async def get_user_history(user_id: str) -> List[dict]:
        if using_mongodb and db_instance is not None:
            try:
                cursor = db_instance.TryOnHistory.find({"userId": user_id}).sort("createdAt", -1)
                history_list = []
                async for doc in cursor:
                    doc["id"] = str(doc.get("_id", doc.get("id")))
                    if "_id" in doc:
                        del doc["_id"]
                    history_list.append(doc)
                return history_list
            except Exception as e:
                print(f"[Database] Mongo get_history error: {e}")

        # Fallback
        return [h for h in _in_memory_history if h.get("userId") == user_id]

    @staticmethod
    async def delete_history_item(item_id: str, user_id: str) -> bool:
        if using_mongodb and db_instance is not None:
            try:
                from bson import ObjectId
                try:
                    res = await db_instance.TryOnHistory.delete_one({"_id": ObjectId(item_id), "userId": user_id})
                    if res.deleted_count > 0:
                        return True
                except Exception:
                    pass
                res = await db_instance.TryOnHistory.delete_one({"id": item_id, "userId": user_id})
                return res.deleted_count > 0
            except Exception as e:
                print(f"[Database] Mongo delete error: {e}")

        # Fallback
        global _in_memory_history
        initial_len = len(_in_memory_history)
        _in_memory_history = [h for h in _in_memory_history if not (h.get("id") == item_id and h.get("userId") == user_id)]
        if len(_in_memory_history) < initial_len:
            save_local_db()
            return True
        return False
