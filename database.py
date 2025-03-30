import os
from typing import Optional, Any, List, Dict
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection, cursor
from dotenv import load_dotenv

from config import DB_CONFIG

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

class DatabaseError(Exception):
    """Exceção base para erros do banco de dados"""
    pass

# Configuração do SQLAlchemy
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency para obter uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Classe para operações com o banco
class Database:
    def __init__(self):
        self._conn_params = DB_CONFIG
        self._conn: Optional[connection] = None

    @property
    def conn(self) -> connection:
        """Retorna uma conexão com o banco de dados"""
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(**self._conn_params)
                # Define o schema correto após a conexão
                with self._conn.cursor() as cur:
                    cur.execute(f"SET search_path TO {os.getenv('DB_SCHEMA')}")
                self._conn.commit()
            except psycopg2.Error as e:
                raise DatabaseError(f"Erro ao conectar ao banco de dados: {e}")
        return self._conn

    @contextmanager
    def cursor(self, commit: bool = True) -> cursor:
        """
        Gerenciador de contexto para cursor do banco de dados
        
        Args:
            commit: Se True, faz commit após operações. Se False, deixa para o chamador gerenciar a transação.
        """
        cur = None
        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)
            yield cur
            if commit:
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise DatabaseError(f"Erro na operação do banco de dados: {e}")
        finally:
            if cur is not None:
                cur.close()

    def fetch(self, query: str, params: Optional[Any] = None) -> List[Dict]:
        """
        Executa uma query SELECT e retorna os resultados
        
        Args:
            query: Query SQL a ser executada
            params: Parâmetros para a query
            
        Returns:
            Lista de dicionários com os resultados
        """
        with self.cursor(commit=False) as cur:
            cur.execute(query, params)
            return cur.fetchall() if cur.description else []

    def execute(self, query: str, params: Optional[Any] = None) -> int:
        """
        Executa uma query de modificação (INSERT/UPDATE/DELETE)
        
        Args:
            query: Query SQL a ser executada
            params: Parâmetros para a query
            
        Returns:
            Número de linhas afetadas
        """
        with self.cursor() as cur:
            cur.execute(query, params)
            return cur.rowcount

    def execute_many(self, query: str, params_list: List[Any]) -> int:
        """
        Executa uma query múltiplas vezes com diferentes parâmetros
        
        Args:
            query: Query SQL a ser executada
            params_list: Lista de parâmetros
            
        Returns:
            Número total de linhas afetadas
        """
        with self.cursor() as cur:
            cur.executemany(query, params_list)
            return cur.rowcount

    def close(self) -> None:
        """Fecha a conexão com o banco de dados"""
        if self._conn is not None and not self._conn.closed:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> 'Database':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()

    def test_connection(self):
        """Testa a conexão e lista as tabelas do schema"""
        with self.cursor() as cur:
            # Mostra o schema configurado no .env
            print(f"Schema configurado no .env: {os.getenv('DB_SCHEMA')}")
            
            # Lista todos os schemas
            cur.execute("SELECT current_schema()")
            current_schema = cur.fetchone()
            print(f"Schema atual: {current_schema}")
            
            # Lista todas as tabelas do schema atual
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s
            """, [os.getenv('DB_SCHEMA')])
            tables = cur.fetchall()
            print(f"Tabelas encontradas: {tables}")
            return tables

# Instância global do banco de dados
db = Database() 