from fastapi import APIRouter
router = APIRouter(prefix="/system")
@router.get("/health")
def health():
    from backend.services.model_service import model_service
    return {"status": "ok", "database": "configured", "ml_service": "ready" if model_service.available else "unavailable"}


@router.get("/model")
def model_status():
    from backend.services.model_service import model_service
    from backend.services.model_service import ModelUnavailable
    if not model_service.available:
        try:
            model_service.load()
        except ModelUnavailable:
            pass
    return {"available": model_service.available, "model_version": model_service.model_version if model_service.available else None, "mode": "ECG_ONLY", "release_status": model_service.release_status, "artifact_integrity": model_service.artifact_integrity, "disclaimer": "Research prototype candidate; not release-eligible and not a medical diagnosis."}
