from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import get_user_by_token, get_token_header
from models import CharacterCreate, CharacterResponse

router = APIRouter()

@router.get("/", response_model=list[CharacterResponse])
async def get_characters(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_header)
):
    """Retorna todos os personagens disponíveis"""
    try:
        # Obter usuário pelo token
        user = get_user_by_token(db=db, token=token)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        # TODO: Implementar lógica de busca de personagens
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=CharacterResponse)
async def create_character(
    character: CharacterCreate,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_header)
):
    """Cria um novo personagem"""
    try:
        # Obter usuário pelo token
        user = get_user_by_token(db=db, token=token)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        # TODO: Implementar lógica de criação de personagem
        return character
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_header)
):
    """Retorna um personagem específico"""
    try:
        # Obter usuário pelo token
        user = get_user_by_token(db=db, token=token)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        # TODO: Implementar lógica de busca de personagem específico
        return None
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))