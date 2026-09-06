from fastapi import APIRouter
router = APIRouter(prefix="/alerts")
@router.get("/rules")
def rules(): return []