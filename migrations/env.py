import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, event, MetaData, text
from sqlalchemy.schema import CreateIndex, CreateTable

from alembic import context

from dotenv import load_dotenv
from models import Base, metadata, User, Session, ChatHistory

# Carrega as variaveis de ambiente
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = metadata

def include_name(name, type_, parent_names):
    """Define quais schemas e objetos devem ser incluídos na migração"""
    if type_ == "schema":
        # Inclui apenas o schema agents_ia
        return name == os.getenv("DB_SCHEMA")
    
    # Para outros objetos (tabelas, índices, etc)
    return True

def include_object(object, name, type_, reflected, compare_to):
    """Define quais objetos devem ser incluidos na migracao"""
    # Inclui apenas objetos do nosso schema
    if hasattr(object, "schema") and object.schema != os.getenv("DB_SCHEMA"):
        return False
    
    return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
        include_object=include_object,
        version_table_schema=os.getenv("DB_SCHEMA")
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
            include_object=include_object,
            version_table_schema=os.getenv("DB_SCHEMA")
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
