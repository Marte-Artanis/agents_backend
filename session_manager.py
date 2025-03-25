import os
import redis
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from database import db

class SessionManager:
    def __init__(self):
        # Conexão com Redis
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT')),
            db=0,
            decode_responses=True
        )
        self.session_expiry = timedelta(hours=24)

    def create_session(self, user_id: int, token: str) -> bool:
        """
        Cria uma nova sessão no Redis e PostgreSQL
        """
        expires_at = datetime.utcnow() + self.session_expiry
        
        try:
            # Salva no Redis
            session_data = {
                'user_id': user_id,
                'status': 'active',
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.redis.setex(
                f"session:{token}",
                self.session_expiry,
                json.dumps(session_data)
            )

            # Salva no PostgreSQL
            db.execute(
                '''
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                ''',
                (user_id, token, expires_at)
            )
            
            return True
        except Exception as e:
            print(f"Erro ao criar sessão: {e}")
            return False

    def validate_session(self, token: str) -> bool:
        """
        Verifica se uma sessão é válida (primeiro no Redis, depois no PostgreSQL)
        """
        try:
            # Verifica no Redis
            redis_data = self.redis.get(f"session:{token}")
            if redis_data:
                # Renova o TTL no Redis
                self.redis.expire(f"session:{token}", self.session_expiry)
                return True

            # Se não está no Redis, verifica no PostgreSQL
            rows = db.fetch(
                '''
                SELECT user_id 
                FROM sessions 
                WHERE token = %s 
                AND status = 'active' 
                AND expires_at > NOW()
                ''',
                (token,)
            )

            # Se encontrou a sessão
            if rows and len(rows) > 0:
                session = rows[0]  # Pega o primeiro resultado
                # Se encontrou no PostgreSQL, recria no Redis
                self.create_session(session['user_id'], token)
                return True

            return False
        except Exception as e:
            print(f"Erro ao validar sessão: {e}")
            return False

    def get_session_data(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Recupera os dados da sessão (primeiro do Redis, depois do PostgreSQL)
        """
        try:
            # Tenta pegar do Redis
            redis_data = self.redis.get(f"session:{token}")
            if redis_data:
                return json.loads(redis_data)

            # Se não está no Redis, pega do PostgreSQL
            rows = db.fetch(
                '''
                SELECT s.user_id, u.email, u.first_name, u.last_name, s.created_at
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token = %s AND s.status = 'active' AND s.expires_at > NOW()
                ''',
                (token,)
            )

            # Se encontrou a sessão
            if rows and len(rows) > 0:
                session = rows[0]  # Pega o primeiro resultado
                # Recria no Redis
                session_data = {
                    'user_id': session['user_id'],
                    'email': session['email'],
                    'first_name': session['first_name'],
                    'last_name': session['last_name'],
                    'status': 'active',
                    'created_at': session['created_at'].isoformat() if session['created_at'] else datetime.utcnow().isoformat()
                }
                
                self.redis.setex(
                    f"session:{token}",
                    self.session_expiry,
                    json.dumps(session_data)
                )
                
                return session_data

            return None
        except Exception as e:
            print(f"Erro ao recuperar dados da sessão: {e}")
            return None

    def end_session(self, token: str) -> bool:
        """
        Finaliza uma sessão (remove do Redis e atualiza status no PostgreSQL)
        """
        try:
            # Remove do Redis
            self.redis.delete(f"session:{token}")

            # Atualiza status no PostgreSQL
            db.execute(
                'UPDATE sessions SET status = %s WHERE token = %s',
                ('expired', token)
            )
            
            return True
        except Exception as e:
            print(f"Erro ao finalizar sessão: {e}")
            return False

    def cleanup_sessions(self):
        """
        Limpa sessões expiradas (não necessário com Redis, ele faz automaticamente)
        Mas atualiza o status no PostgreSQL para manter o histórico
        """
        try:
            db.execute(
                '''
                UPDATE sessions 
                SET status = 'expired' 
                WHERE status = 'active' AND expires_at <= NOW()
                '''
            )
        except Exception as e:
            print(f"Erro ao limpar sessões: {e}")

# Instância global do gerenciador de sessões
session_manager = SessionManager() 