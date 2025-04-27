from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from models import UserUpdate, UserResponse

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_profile(
    user = Depends(get_current_user)
):
    """Retorna o perfil do usuário atual"""
    try:
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza o perfil do usuário"""
    try:
        # TODO: Implementar lógica de atualização de perfil
        return user
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_settings(
    user = Depends(get_current_user)
):
    """Retorna as configurações do usuário"""
    try:
        # TODO: Implementar lógica de busca de configurações
        return {}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/settings")
async def update_settings(
    settings: dict,
    user = Depends(get_current_user)
):
    """Atualiza as configurações do usuário"""
    try:
        # TODO: Implementar lógica de atualização de configurações
        return settings
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 