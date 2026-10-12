from fastapi import APIRouter, HTTPException, Depends, status
from database import DatabaseManager
from utils.auth import get_current_user_id

router = APIRouter(prefix="/api/history", tags=["Try-On History"])

@router.get("")
async def get_history(user_id: str = Depends(get_current_user_id)):
    """Retrieves all past virtual try-on items for the current user."""
    history = await DatabaseManager.get_user_history(user_id)
    return {
        "count": len(history),
        "history": history
    }

@router.delete("/{item_id}")
async def delete_history(item_id: str, user_id: str = Depends(get_current_user_id)):
    """Deletes a try-on history record."""
    success = await DatabaseManager.delete_history_item(item_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="History record not found or unauthorized.")
    return {"message": "Try-on record deleted successfully."}
