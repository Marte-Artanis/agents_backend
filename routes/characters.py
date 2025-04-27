from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from models.schemas import CharacterCreate, CharacterResponse
from prompts.character_descriptions import character_descriptions_prompts
from prompts.available_periods import available_periods_prompts
from prompts.character_historical_factors import character_historical_factors_prompts
from prompts.language_descriptions import language_descriptions_prompts
from datetime import datetime

router = APIRouter()

@router.get("/languages")
async def get_languages(user = Depends(get_current_user)):
    return language_descriptions_prompts

@router.get("/", response_model=list[CharacterResponse])
async def get_characters(
    user = Depends(get_current_user)
):
    """Retorna todos os personagens disponíveis"""
    try:
        characters = []
        for char_name, description in character_descriptions_prompts.items():
            characters.append(CharacterResponse(
                id=len(characters) + 1,  # ID temporário
                name=char_name,
                description=description.split("\n")[0].strip(),
                historical_periods=available_periods_prompts.get(char_name, []),
                historical_factors=character_historical_factors_prompts.get(char_name, []),
                languages=list(language_descriptions_prompts.keys()),
                created_at=datetime.now(),
                updated_at=datetime.now()
            ))
        return characters
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=CharacterResponse)
async def create_character(
    character: CharacterCreate,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cria um novo personagem"""
    try:
        # TODO: Implementar lógica de criação de personagem
        return character
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: str,
    user = Depends(get_current_user)
):
    """Retorna um personagem específico"""
    try:
        # Encontra o personagem pelo nome (que é o character_id)
        if character_id not in character_descriptions_prompts:
            raise HTTPException(status_code=404, detail="Personagem não encontrado")
            
        description = character_descriptions_prompts[character_id]
        return CharacterResponse(
            id=1,  # ID temporário
            name=character_id,
            description=description.split("\n")[0].strip(),
            historical_periods=available_periods_prompts.get(character_id, []),
            historical_factors=character_historical_factors_prompts.get(character_id, []),
            languages=list(language_descriptions_prompts.keys()),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historical-periods/{character}")
async def get_historical_periods(character: str, user = Depends(get_current_user)):
    # Tenta buscar pelo nome
    if character in available_periods_prompts:
        return available_periods_prompts[character]
    # Tenta buscar por índice
    try:
        idx = int(character)
        all_names = list(available_periods_prompts.keys())
        if 0 <= idx < len(all_names):
            name = all_names[idx]
            return available_periods_prompts.get(name, [])
    except Exception:
        pass
    return []

@router.get("/historical-factors/{character}")
async def get_historical_factors(character: str, user = Depends(get_current_user)):
    # Tenta buscar pelo nome
    if character in character_historical_factors_prompts:
        return character_historical_factors_prompts[character]
    # Tenta buscar por índice
    try:
        idx = int(character)
        all_names = list(character_historical_factors_prompts.keys())
        if 0 <= idx < len(all_names):
            name = all_names[idx]
            return character_historical_factors_prompts.get(name, [])
    except Exception:
        pass
    return []