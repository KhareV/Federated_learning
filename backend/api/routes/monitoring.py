from fastapi import APIRouter
router = APIRouter(prefix="/monitoring")
@router.get("/sessions")
def sessions(): return []