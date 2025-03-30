import os
import shutil
from pathlib import Path
from alembic.config import Config
from alembic import command
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from urllib.parse import quote_plus

from config import DB_CONFIG, APP_CONFIG
from models import Base

def clean_alembic_history():
    """Limpa o histórico do Alembic no banco de dados"""
    from database import Database
    
    db = Database()
    try:
        with db.cursor() as cur:
            # Limpa a tabela alembic_version do schema correto
            schema = APP_CONFIG['DB_SCHEMA']
            cur.execute(f"DROP TABLE IF EXISTS {schema}.alembic_version")
            db.conn.commit()
    finally:
        db.close()

def create_alembic_ini():
    """Cria o arquivo alembic.ini com as configurações corretas"""
    DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    
    alembic_ini_content = f"""[alembic]
script_location = migrations
sqlalchemy.url = {DATABASE_URL}

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
    
    with open('alembic.ini', 'w') as f:
        f.write(alembic_ini_content)

def create_env_py(migrations_dir: Path):
    """Cria o arquivo env.py com as configurações do Alembic"""
    env_py_content = """import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""
    
    env_py_path = migrations_dir / 'env.py'
    with open(env_py_path, 'w') as f:
        f.write(env_py_content)

def create_script_mako(migrations_dir: Path):
    """Cria o arquivo script.py.mako para template das migrações"""
    script_mako_content = """\"\"\"${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

\"\"\"
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
"""
    
    script_mako_path = migrations_dir / 'script.py.mako'
    with open(script_mako_path, 'w') as f:
        f.write(script_mako_content)

def migrate():
    """Executa as migrações do banco de dados"""
    # Cria o diretório migrations se não existir
    migrations_dir = Path('migrations')
    migrations_dir.mkdir(exist_ok=True)
    
    # Verifica se os arquivos necessários existem
    env_py_exists = (migrations_dir / 'env.py').exists()
    script_mako_exists = (migrations_dir / 'script.py.mako').exists()
    
    # Se algum arquivo necessário não existe, recria o diretório
    if not (env_py_exists and script_mako_exists):
        shutil.rmtree(migrations_dir)
        migrations_dir.mkdir()
        
        # Cria os arquivos necessários
        create_alembic_ini()
        create_env_py(migrations_dir)
        create_script_mako(migrations_dir)
        
        # Inicializa o Alembic
        alembic_cfg = Config("alembic.ini")
        command.init(alembic_cfg, "migrations")
        
        # Cria a primeira migração
        command.revision(alembic_cfg, 
                        message="initial_migration",
                        autogenerate=True)
    
    # Executa as migrações
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

if __name__ == '__main__':
    migrate() 