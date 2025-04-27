from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from dependencies import get_current_user
from agents_structures import generate_character_response, AgentMemory
from models import ChatRequest
import uuid

router = APIRouter()

@router.get("/")
async def get_user_chats(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Retorna todos os chats do usuário"""
    try:
        # Criar instância de AgentMemory para buscar chats
        memory = AgentMemory(
            character_name="",  # Não importa aqui
            chat_id="",        # Não importa aqui
            user_id=user['id']
        )
        
        # Buscar todos os chats do usuário
        return memory.get_user_chats()
        
    except Exception as e:
        print(f"Erro ao buscar chats do usuário: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{chat_id}")
async def get_chat_history(
    chat_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Retorna o histórico completo de um chat"""
    try:
        # Criar instância de AgentMemory para buscar mensagens
        memory = AgentMemory(
            character_name="",  # Não importa aqui
            chat_id=chat_id,
            user_id=user['id']
        )
        
        # Buscar mensagens do Pinecone 
        messages = memory.get_chat_history()
        
        # Não lançar erro se não houver mensagens, apenas retornar objeto vazio
        return messages
        
    except Exception as e:
        print(f"Erro ao buscar histórico do chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Deleta um chat do usuário"""
    try:
        # Criar instância de AgentMemory
        memory = AgentMemory(
            character_name="",
            chat_id=chat_id,
            user_id=user['id']
        )
        
        print(f"Solicitação para deletar chat {chat_id} do usuário {user['id']}")
        
        # Tentar deletar chat, mas mesmo com falha, retornar sucesso ao frontend
        try:
            result = memory.delete_chat()
            print(f"Resultado da exclusão: {result}")
        except Exception as deletion_error:
            print(f"Erro ao tentar deletar chat: {str(deletion_error)}")
            # Não lançar exceção para o frontend
        
        # Sempre retornar sucesso para que o frontend possa atualizar sua interface
        return {"status": "success"}
        
    except Exception as e:
        print(f"Erro no endpoint de deletar chat: {str(e)}")
        # Ainda retorna sucesso para o frontend
        return {"status": "success", "warning": str(e)}

@router.post("/chat")
async def chat(
    request: ChatRequest,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Gerar chat_id se não existir
        chat_id = request.chat_id or str(uuid.uuid4())
        
        # Criar instância do AgentMemory
        memory = AgentMemory(
            character_name=request.character,
            chat_id=chat_id,
            user_id=user['id']
        )
        
        # Se for um novo chat, criar o registro inicial
        if not request.chat_id:
            success = memory.create_chat(
                historical_period=request.historical_period,
                historical_factor=request.historical_factors,
                language=request.language
            )
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Erro ao criar novo chat"
                )
        
        # Obter histórico relevante
        relevant_history = memory.get_relevant_memories(request.prompt)
        
        # Gerar resposta
        response = generate_character_response(
            character=request.character,
            prompt=request.prompt,
            historical_period=request.historical_period,
            historical_factor=request.historical_factors,
            language=request.language,
            memory=memory
        )
        
        # Salvar a interação
        memory.add_memory(
            user_input=request.prompt,
            response=response,
            context=f"Período: {request.historical_period}, Fator Histórico: {request.historical_factors}"
        )
        
        return {
            "chat_id": chat_id,
            "response": response
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )