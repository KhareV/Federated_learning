from fastapi import APIRouter
router = APIRouter(prefix="/experiments")
@router.get("")
def exps(): return []