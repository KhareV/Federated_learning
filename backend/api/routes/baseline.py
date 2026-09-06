from fastapi import APIRouter
router = APIRouter(prefix="/baseline")
@router.get("/{user_id}")
def baseline(): return {}