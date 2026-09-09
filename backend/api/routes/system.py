from fastapi import APIRouter
router = APIRouter(prefix="/system")
@router.get("/health")
def health():
    from backend.services.model_service import model_service
    return {"status": "ok", "database": "configured", "ml_service": "ready" if model_service.available else "unavailable"}
