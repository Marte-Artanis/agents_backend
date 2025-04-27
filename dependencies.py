from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from database import db
from typing import Dict, Any

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """
    Função de dependência para obter o usuário atual baseado no token JWT.
    Pode ser usada em qualquer rota que precise de autenticação.
    """
    token = credentials.credentials
    try:
        with db.cursor() as cur:
            # Verifica se o token é válido
            cur.execute("""
                SELECT u.* 
                FROM users u
                JOIN sessions s ON s.user_id = u.id
                WHERE s.token = %s AND s.is_active = true
                  AND s.expires_at > NOW()
            """, [token])
            user = cur.fetchone()
            
            if not user:
                raise HTTPException(status_code=401, detail="Token inválido ou expirado")
                
            return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
