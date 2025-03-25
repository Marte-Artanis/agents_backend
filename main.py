from fastapi import FastAPI, HTTPException, Depends, Header, Security
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
from auth import auth
from migrate import run_migrations

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Executa as migrations quando a aplicação inicia"""
    print("Iniciando aplicação...")
    run_migrations()
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
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With"
    ],
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
    session_id: Optional[str] = None

class Message(BaseModel):
    role: str
    content: str

async def get_token_header(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    # Primeiro valida o token JWT
    user = auth.get_user_by_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Depois valida/cria a sessão
    if not session_manager.validate_session(credentials.credentials):
        session_manager.create_session(user['id'], credentials.credentials)
    
    return credentials.credentials

@app.get("/new-session")
async def create_new_session():
    session_id = session_manager.create_session()
    return {"session_id": session_id}

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    if not session_manager.validate_session(session_id):
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return {"status": "active"}

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
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

@app.post("/chat/")
async def chat(request: ChatRequest, token: str = Depends(get_token_header)):
    # Obter user_id do token
    user = auth.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Verificar se tem session_id
    if not request.session_id:
        # Criar nova sessão com o user_id e token
        if not session_manager.create_session(user['id'], token):
            raise HTTPException(status_code=500, detail="Erro ao criar sessão")
        session_id = token
    else:
        if not session_manager.validate_session(request.session_id):
            raise HTTPException(status_code=400, detail="Sessão inválida ou expirada")
        session_id = request.session_id

    # Criar/carregar memória do personagem com o session_id e user_id
    memory = AgentMemory(request.character, session_id, user['id'])

    # Gerar resposta
    response = generate_character_response(
        character=request.character,
        user_input=request.prompt,
        historical_period=request.historical_period,
        historical_factor=request.historical_factors,
        language=request.language,
        memory=memory
    )

    # Recuperar histórico atualizado
    chat_history = memory.get_chat_history()

    return {
        "response": response,
        "session_id": session_id,
        "messages": chat_history
    }

@app.post("/register")
async def register(user_data: UserRegistration):
    try:
        print(f"Recebendo requisição de registro: {user_data}")
        result = auth.register_user(
            user_data.first_name,
            user_data.last_name,
            user_data.email,
            user_data.password,
            user_data.birth_date
        )
        print(f"Registro bem sucedido: {result}")
        return {
            "user": {
                "id": result['id'],
                "email": result['email']
            },
            "token": result['token']
        }
    except Exception as e:
        print(f"Erro no registro: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login(login_data: UserLogin):
    result = auth.login_user(login_data.email, login_data.password)
    return result  # Retorna diretamente o objeto que já está formatado corretamente

@app.post("/logout")
async def logout(token: str = Depends(get_token_header)):
    if auth.logout_user(token):
        return {"message": "Logout realizado com sucesso"}
    raise HTTPException(status_code=400, detail="Erro ao realizar logout")

@app.get("/me")
async def get_current_user(token: str = Depends(get_token_header)):
    user = auth.get_user_by_token(token)
    return user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)