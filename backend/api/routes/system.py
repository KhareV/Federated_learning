from fastapi import APIRouter
router = APIRouter(prefix="/system")
@router.get("/health")
def health():
    from backend.services.model_service import model_service
    return {"status": "ok", "database": "configured", "ml_service": "ready" if model_service.available else "unavailable"}


@router.get("/model")
def model_status():
    from backend.services.model_service import model_service
    return {"available": model_service.available, "model_version": model_service.model_version if model_service.available else None, "mode": "ECG_ONLY", "release_status": model_service.release_status, "disclaimer": "Research prototype candidate; not release-eligible and not a medical diagnosis."}
