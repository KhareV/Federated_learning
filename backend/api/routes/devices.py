from fastapi import APIRouter
router = APIRouter(prefix="/devices")
@router.get("")
def devices(): return []