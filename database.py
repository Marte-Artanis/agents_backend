import os
from typing import Optional, Any, List, Dict
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection, cursor
from dotenv import load_dotenv

load_dotenv()

class DatabaseError(Exception):
    """Exceção base para erros do banco de dados"""
    pass

class Database:
    def __init__(self):
        self._conn_params = {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }
        self._conn: Optional[connection] = None

    @property
    def conn(self) -> connection:
        """Retorna uma conexão com o banco de dados"""
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(**self._conn_params)
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

# Instância global do banco de dados
db = Database() 