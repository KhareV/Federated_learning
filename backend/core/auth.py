from typing import Optional
from pydantic import BaseModel

class TokenData(BaseModel):
    username: str
    role: str

def create_access_token(data: dict, role: str) -> str:
    return "fake-token"

def verify_token(token: str) -> TokenData:
    return TokenData(username="admin", role="ADMIN")