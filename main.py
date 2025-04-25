from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models.database import Base
from routes import auth_router, chat_router, characters_router, users_router

# Criar tabelas no banco de dados
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(characters_router, prefix="/characters", tags=["characters"])
app.include_router(users_router, prefix="/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Bem-vindo à API do Project Infinity"}