import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from database import db
from fastapi import HTTPException

# Configurações de JWT
JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = timedelta(days=1)

class Auth:
    @staticmethod
    def hash_password(password: str) -> str:
        """Gera o hash da senha"""
        print("Gerando hash para senha")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        print(f"Hash gerado: {hashed}")
        return hashed.decode('utf-8')

    @staticmethod
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

    @staticmethod
    def create_token(user_id: int) -> str:
        """Cria um token JWT"""
        print(f"Criando token para usuário {user_id}")
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + JWT_EXPIRATION
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> dict:
        """Verifica se o token é válido"""
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    @staticmethod
    def register_user(first_name: str, last_name: str, email: str, password: str, birth_date: datetime) -> dict:
        print(f"Tentando registrar usuário: {email}")
        
        # Verifica se o email já existe
        existing_user = db.fetch("SELECT id FROM users WHERE email = %s", [email])
        print(f"Usuário existente? {existing_user}")
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email já cadastrado"
            )

        # Cria o usuário
        hashed_password = Auth.hash_password(password)
        print(f"Hash gerado para senha: {hashed_password}")
        
        query = """
            INSERT INTO users (first_name, last_name, email, password_hash, birth_date)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, email
        """
        params = [first_name, last_name, email, hashed_password, birth_date]
        print(f"Executando query: {query}")
        print(f"Com parâmetros: {params}")
        
        result = db.fetch(query, params)
        print(f"Resultado do insert: {result}")
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Erro ao criar usuário"
            )
            
        user = result[0]
        print(f"Usuário criado: {user}")
        
        # Gera o token
        token = Auth.create_token(user['id'])
        print(f"Token gerado: {token}")

        # Registra a sessão
        session_query = """
            INSERT INTO sessions (user_id, token, expires_at)
            VALUES (%s, %s, %s)
        """
        session_params = [user['id'], token, datetime.utcnow() + JWT_EXPIRATION]
        print(f"Registrando sessão com: {session_params}")
        
        db.execute(session_query, session_params)
        
        return {
            'id': user['id'],
            'email': user['email'],
            'token': token
        }

    @staticmethod
    def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Autentica um usuário e retorna o token"""
        print(f"Tentando login para: {email}")
        
        # Busca o usuário
        query = "SELECT id, email, password_hash FROM users WHERE email = %s"
        print(f"Executando query: {query}")
        print(f"Com email: {email}")
        
        user = db.fetch(query, [email])
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Email ou senha incorretos"
            )

        # Verifica a senha
        if not Auth.verify_password(password, user[0]['password_hash']):
            raise HTTPException(
                status_code=401,
                detail="Email ou senha incorretos"
            )

        # Gera o token
        token = Auth.create_token(user[0]['id'])
        print(f"Token gerado: {token}")

        # Registra a sessão
        session_query = """
            INSERT INTO sessions (user_id, token, expires_at)
            VALUES (%s, %s, %s)
        """
        session_params = [user[0]['id'], token, datetime.utcnow() + JWT_EXPIRATION]
        print(f"Registrando sessão com: {session_params}")
        
        db.execute(session_query, session_params)
        return {
            'user': {
                'id': user[0]['id'],
                'email': user[0]['email']
            },
            'token': token
        }

    @staticmethod
    def logout_user(token: str) -> bool:
        """Remove a sessão do usuário"""
        return db.execute(
            "UPDATE sessions SET status = 'expired' WHERE token = %s",
            [token]
        ) > 0

    @staticmethod
    def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
        """Recupera o usuário pelo token"""
        payload = Auth.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Usuário não encontrado"
            )

        user = db.fetch(
            """
            SELECT u.id, u.first_name, u.last_name, u.email, u.created_at
            FROM users u
            JOIN sessions s ON s.user_id = u.id
            WHERE s.token = %s AND s.status = 'active' AND s.expires_at > NOW()
            """,
            [token]
        )

        return user[0] if user else None

# Instância global de autenticação
auth = Auth() 