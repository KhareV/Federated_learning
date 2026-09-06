from fastapi import APIRouter
router = APIRouter(prefix="/fl")
@router.get("/status")
def status(): return {}