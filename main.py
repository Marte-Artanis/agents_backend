from fastapi import FastAPI, HTTPException, Depends, Header, Security, Request, Body
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from agents_structures import generate_character_response, AgentMemory
from prompts.available_periods import available_periods_prompts
from prompts.character_descriptions import character_descriptions_prompts
from prompts.character_historical_factors import character_historical_factors_prompts
from prompts.language_descriptions import language_descriptions_prompts
from typing import Optional, List, Dict
from session_manager import SessionManager
from datetime import datetime
from auth import (
    register_user,
    login_user,
    get_user_by_token,
    logout_user,
    verify_password,
    hash_password
)
from database import db, get_db
from sqlalchemy.orm import Session

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa a aplicação"""
    print("Iniciando aplicação...")
    yield
    print("Finalizando aplicação...")

app = FastAPI(lifespan=lifespan)
session_manager = SessionManager()
security = HTTPBearer()

# Configuração CORS para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With"
    ]
)

# Modelos Pydantic
class UserRegistration(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    birth_date: datetime

class UserLogin(BaseModel):
    email: str
    password: str

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

class UserUpdate(BaseModel):
    first_name: str
    last_name: str
    current_password: str
    new_password: Optional[str] = None

async def get_token_header(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> str:
    try:
        if not credentials:
            raise HTTPException(status_code=401, detail="Token não fornecido")
            
        token = credentials.credentials
        if not token:
            raise HTTPException(status_code=401, detail="Token não fornecido")
            
        # Tenta obter o usuário com o token
        user = get_user_by_token(db=db, token=token)
        if not user:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        # Valida/cria a sessão
        if not session_manager.validate_session(token):
            session_manager.create_session(user.id, token)
        
        return token
        
    except Exception as e:
        print(f"Erro em get_token_header: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/new-session")
async def create_new_session(token: str = Depends(get_token_header)):
    session_id = session_manager.create_session()
    return {"session_id": session_id}

@app.get("/session/{session_id}")
async def get_session(
    session_id: str,
    token: str = Depends(get_token_header)
):
    if not session_manager.validate_session(session_id):
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return {"status": "active"}

@app.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    token: str = Depends(get_token_header)
):
    if session_manager.delete_session(session_id):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Sessão não encontrada")

@app.get("/characters")
async def get_characters(token: str = Depends(get_token_header)):
    characters = {}
    for char_name, description in character_descriptions_prompts.items():
        characters[char_name] = {
            "name": char_name,
            "description": description.split("\n")[0].strip()
        }
    return characters

@app.get("/historical-periods/{character}")
async def get_historical_periods(character: str, token: str = Depends(get_token_header)):
    if character in available_periods_prompts:
        return available_periods_prompts[character]
    return []

@app.get("/historical-factors/{character}")
async def get_historical_factors(character: str, token: str = Depends(get_token_header)):
    if character in character_historical_factors_prompts:
        return character_historical_factors_prompts[character]
    return []

@app.get("/languages")
async def get_languages(token: str = Depends(get_token_header)):
    return language_descriptions_prompts

@app.get("/chats")
async def get_user_chats(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_header)
):
    """Retorna todos os chats do usuário"""
    try:
        # Obter usuário pelo token
        user = get_user_by_token(db=db, token=token)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        # Criar instância de AgentMemory para buscar chats
        memory = AgentMemory(
            character_name="",  # Não importa aqui
            chat_id="",        # Não importa aqui
            user_id=user.id
        )
        
        # Buscar todos os chats do usuário
        return memory.get_user_chats()
        
    except Exception as e:
        print(f"Erro ao buscar chats do usuário: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/{chat_id}")
async def get_chat_history(
    chat_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_header)
):
    """Retorna o histórico completo de um chat"""
    try:
        # Obter usuário pelo token
        user = get_user_by_token(db=db, token=token)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        # Criar instância de AgentMemory para buscar mensagens
        memory = AgentMemory(
            character_name="",  # Não importa aqui
            chat_id=chat_id,
            user_id=user.id
        )
        
        # Buscar mensagens do Pinecone 
        messages = memory.get_chat_history()
        
        # Não lançar erro se não houver mensagens, apenas retornar objeto vazio
        return messages
        
    except Exception as e:
        print(f"Erro ao buscar histórico do chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/{chat_id}")
async def delete_chat(
    chat_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(get_token_header)
):
    """Deleta um chat do usuário"""
    try:
        # Obter usuário pelo token
        user = get_user_by_token(db=db, token=token)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        # Criar instância de AgentMemory
        memory = AgentMemory(
            character_name="",
            chat_id=chat_id,
            user_id=user.id
        )
        
        print(f"Solicitação para deletar chat {chat_id} do usuário {user.id}")
        
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

@app.post("/chat")
async def chat(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    try:
        # Obter usuário pelo token
        user = get_user_by_token(db=db, token=credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
        # Gerar novo chat_id se não fornecido
        chat_id = chat_request.chat_id
        if not chat_id:
            chat_id = f"{user.id}_{datetime.utcnow().timestamp()}"
            
        # Criar/carregar memória do personagem
        memory = AgentMemory(
            character_name=chat_request.character,
            chat_id=chat_id,
            user_id=user.id
        )

        # Gerar resposta
        response = generate_character_response(
            character=chat_request.character,
            prompt=chat_request.prompt,
            historical_period=chat_request.historical_period,
            historical_factor=chat_request.historical_factors,
            language=chat_request.language,
            memory=memory
        )

        return {
            "response": response,
            "chat_id": chat_id
        }

    except Exception as e:
        print(f"Erro no chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/register")
async def register(
    user_data: UserRegistration = Body(...),
    db: Session = Depends(get_db)
):
    """Registra um novo usuário"""
    try:
        return register_user(
            db=db,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            password=user_data.password,
            birth_date=user_data.birth_date
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login")
async def login(
    user_data: UserLogin = Body(...),
    db: Session = Depends(get_db)
):
    """Autentica um usuário"""
    try:
        return login_user(db, user_data.email, user_data.password)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/auth/logout")
async def logout(
    token: str = Depends(get_token_header),
    db: Session = Depends(get_db)
):
    """Desativa a sessão do usuário"""
    return logout_user(db, token)

@app.get("/auth/me")
async def get_current_user(
    token: str = Depends(get_token_header),
    db: Session = Depends(get_db)
):
    """Retorna os dados do usuário atual"""
    user = get_user_by_token(db=db, token=token)
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user

@app.put("/auth/me")
async def update_user(
    user_data: UserUpdate,
    token: str = Depends(get_token_header),
    db: Session = Depends(get_db)
):
    """Atualiza os dados do usuário"""
    user = get_user_by_token(db=db, token=token)
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    
    # Verifica a senha atual
    if not verify_password(user_data.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Senha atual incorreta")
    
    # Atualiza os dados
    user.first_name = user_data.first_name
    user.last_name = user_data.last_name
    
    # Se uma nova senha foi fornecida, atualiza
    if user_data.new_password:
        user.password_hash = hash_password(user_data.new_password)
    
    db.commit()
    db.refresh(user)
    return user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)