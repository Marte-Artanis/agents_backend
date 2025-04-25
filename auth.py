import os
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session as DbSession
from sqlalchemy import update
from models import User, Session
from database import get_db
from session_manager import SessionManager

# Configurações de JWT
JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = 'HS256'
TOKEN_EXPIRATION = 24  # horas

# Configurações de segurança
security = HTTPBearer()
session_manager = SessionManager()

async def get_token_header(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> str:
    """Valida o token de autenticação e retorna o token"""
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

def hash_password(password: str) -> str:
    """Gera o hash da senha"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        print(f"Erro ao verificar senha: {e}")
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

def register_user(
    db: DbSession, 
    first_name: str, 
    last_name: str, 
    email: str, 
    password: str, 
    birth_date: datetime
) -> dict:
    """Registra um novo usuário"""
    
    # Verifica se o email já existe
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=400,
            detail="Email já cadastrado"
        )

    # Cria o usuário
    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=hash_password(password),
        birth_date=birth_date
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Gera o token e registra a sessão
    token, expires_at = create_jwt_token(user.id)
    register_session(db, user.id, token, expires_at)
    
    return {
        'id': user.id,
        'email': user.email,
        'token': token
    }

def register_session(db: DbSession, user_id: int, token: str, expires_at: datetime) -> Session:
    """Registra uma nova sessão"""
    # Desativa sessões antigas do usuário
    db.execute(
        update(Session)
        .where(Session.user_id == user_id)
        .values(is_active=False)
    )
    
    # Cria nova sessão
    session = Session(
        user_id=user_id,
        token=token,
        is_active=True,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    return session

def login_user(db: DbSession, email: str, password: str) -> dict:
    """Autentica um usuário e retorna o token"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
    token, expires_at = create_jwt_token(user.id)
    register_session(db, user.id, token, expires_at)
    
    return {
        "token": token,
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        }
    }

def get_user_by_token(db: DbSession, token: str) -> User:
    """Retorna o usuário associado ao token se válido"""
    try:
        print("\n=== Debug Token Validation ===")
        print(f"Token recebido: {token[:20]}...")
        
        # Verifica se o token é válido
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        print(f"User ID extraído: {user_id}")
        
        # Busca a sessão
        session = db.query(Session).filter(
            Session.token == token,
            Session.is_active == True
        ).first()
        
        print(f"Sessão encontrada: {session is not None}")
        
        if not session:
            raise HTTPException(status_code=401, detail="Sessão inválida")
            
        # Verifica se o token expirou
        current_time = datetime.utcnow()
        expires_at = session.expires_at.replace(tzinfo=None)  # Remove timezone info
        print(f"Tempo atual: {current_time}")
        print(f"Expira em: {expires_at}")
        
        if current_time > expires_at:
            session.is_active = False
            db.commit()
            raise HTTPException(status_code=401, detail="Token expirado")
            
        # Retorna o usuário
        user = db.query(User).filter(User.id == user_id).first()
        print(f"Usuário encontrado: {user is not None}")
        return user
        
    except ExpiredSignatureError as e:
        print(f"Erro de token expirado: {str(e)}")
        raise HTTPException(status_code=401, detail="Token expirado")
    except InvalidTokenError as e:
        print(f"Erro de token inválido: {str(e)}")
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        print(f"Erro inesperado ao validar token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Erro ao validar token: {str(e)}")

def logout_user(db: DbSession, token: str):
    """Desativa a sessão do usuário"""
    session = db.query(Session).filter(Session.token == token).first()
    if session:
        session.is_active = False
        db.commit() 