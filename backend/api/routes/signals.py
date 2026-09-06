from fastapi import APIRouter
router = APIRouter(prefix="/signals")
@router.get("/ecg/{session_id}")
def ecg(): return {}