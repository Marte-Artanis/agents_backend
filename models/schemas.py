from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    birth_date: datetime

class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    birth_date: datetime
    created_at: datetime
    updated_at: datetime

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatRequest(BaseModel):
    character: str
    prompt: str
    historical_period: str
    historical_factors: str
    language: str
    chat_id: Optional[str] = None

class Message(BaseModel):
    role: str
    content: str

class CharacterCreate(BaseModel):
    name: str
    description: str
    historical_periods: List[str]
    historical_factors: List[str]
    languages: List[str]

class CharacterResponse(BaseModel):
    id: int
    name: str
    description: str
    historical_periods: List[str]
    historical_factors: List[str]
    languages: List[str]
    created_at: datetime
    updated_at: datetime 