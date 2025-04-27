from fastapi import APIRouter, HTTPException, Depends, Security, Form
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db, db
from pydantic import BaseModel
import bcrypt
import jwt
from datetime import datetime, timedelta
import os
from dependencies import get_current_user

router = APIRouter()
security = HTTPBearer()

# Configurações JWT
JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = 'HS256'
TOKEN_EXPIRATION = 24  # horas

# Modelos para validação
class UserLogin(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    birth_date: datetime

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    try:
        print("\n=== DEBUG VERIFY_PASSWORD ===")
        print(f"Senha recebida (length): {len(password)}")
        print(f"Hash recebido: {hashed_password[:20]}...")
        result = bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
        print(f"Resultado da verificação: {result}")
        return result
    except Exception as e:
        print(f"Erro ao verificar senha: {e}")
        print(f"Tipo do erro: {type(e)}")
        return False

def create_jwt_token(user_id: int) -> tuple[str, datetime]:
    """Cria um novo token JWT"""
    expires_at = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION)
    
    payload = {
        "user_id": user_id,
        "exp": expires_at
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expires_at

@router.post("/register")
async def register(user_data: UserCreate):
    try:
        # Verifica se o email já existe
        with db.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", [user_data.email])
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Email já cadastrado")
            
            # Gera o hash da senha
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), salt).decode('utf-8')
            
            # Insere o usuário
            cur.execute("""
                INSERT INTO users (first_name, last_name, email, password_hash, birth_date)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, email
            """, [
                user_data.first_name,
                user_data.last_name,
                user_data.email,
                password_hash,
                user_data.birth_date
            ])
            
            user = cur.fetchone()
            
            # Gera o token
            token, expires_at = create_jwt_token(user['id'])
            
            # Registra a sessão
            cur.execute("""
                INSERT INTO sessions (user_id, token, is_active, expires_at)
                VALUES (%s, %s, true, %s)
            """, [user['id'], token, expires_at])
            
            return {
                "user": {
                    "id": user['id'],
                    "email": user['email']
                },
                "token": token
            }
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(login_data: UserLogin):
    """
    Login usando JSON com os campos:
    - email: email do usuário
    - password: senha do usuário
    """
    try:
        print("\n=== DEBUG LOGIN ROUTE ===")
        print(f"Email recebido: {login_data.email}")
        print(f"Senha recebida: {'*' * len(login_data.password)}")
        
        # Busca o usuário
        with db.cursor() as cur:
            cur.execute("""
                SELECT id, email, first_name, last_name, password_hash 
                FROM users 
                WHERE email = %s
            """, [login_data.email])
            user = cur.fetchone()
            
        print(f"Usuário encontrado: {user is not None}")
        
        if not user or not verify_password(login_data.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        print("Gerando token...")    
        token, expires_at = create_jwt_token(user['id'])
        print(f"Token gerado: {token[:20]}...")
        
        print("Registrando sessão...")
        # Desativa sessões antigas e cria nova sessão
        with db.cursor() as cur:
            cur.execute("""
                UPDATE sessions 
                SET is_active = false 
                WHERE user_id = %s
            """, [user['id']])
            
            cur.execute("""
                INSERT INTO sessions (user_id, token, is_active, expires_at)
                VALUES (%s, %s, true, %s)
            """, [user['id'], token, expires_at])
        
        response_data = {
            "token": token,
            "user": {
                "id": user['id'],
                "first_name": user['first_name'],
                "last_name": user['last_name'],
                "email": user['email']
            }
        }
        print(f"Dados de resposta: {response_data}")
        return response_data
        
    except Exception as e:
        print(f"\n=== ERRO NO LOGIN ===")
        print(f"Tipo do erro: {type(e)}")
        print(f"Erro: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        with db.cursor() as cur:
            cur.execute("""
                UPDATE sessions 
                SET is_active = false 
                WHERE token = %s
            """, [token])
            return {"message": "Logout realizado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    # Retornar apenas os campos públicos do usuário
    public_fields = [
        "id", "email", "first_name", "last_name", "birth_date", "created_at", "updated_at"
    ]
    return {k: v for k, v in user.items() if k in public_fields}