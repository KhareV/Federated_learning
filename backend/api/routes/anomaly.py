from fastapi import APIRouter
router = APIRouter(prefix="/anomaly")
@router.get("/events")
def events(): return []