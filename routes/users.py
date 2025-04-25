from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import get_user_by_token, get_token_header
from models import UserUpdate, UserResponse

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_profile(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_header)
):
    """Retorna o perfil do usuário atual"""
    try:
        user = get_user_by_token(db=db, token=token)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_header)
):
    """Atualiza o perfil do usuário"""
    try:
        user = get_user_by_token(db=db, token=token)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        # TODO: Implementar lógica de atualização de perfil
        return user
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_settings(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_header)
):
    """Retorna as configurações do usuário"""
    try:
        user = get_user_by_token(db=db, token=token)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        # TODO: Implementar lógica de busca de configurações
        return {}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/settings")
async def update_settings(
    settings: dict,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_header)
):
    """Atualiza as configurações do usuário"""
    try:
        user = get_user_by_token(db=db, token=token)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        # TODO: Implementar lógica de atualização de configurações
        return settings
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 