import os
from dotenv import load_dotenv

load_dotenv()

# Configurações do Banco de Dados
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'options': f"-c search_path={os.getenv('DB_SCHEMA')}"
}

# Configurações da Aplicação
APP_CONFIG = {
    'SECRET_KEY': os.getenv('SECRET_KEY'),
    'ALGORITHM': os.getenv('ALGORITHM'),
    'ACCESS_TOKEN_EXPIRE_MINUTES': int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30')),
    'DB_SCHEMA': os.getenv('DB_SCHEMA')
}

# Configurações do Supabase
SUPABASE_CONFIG = {
    'url': os.getenv('SUPABASE_URL'),
    'key': os.getenv('SUPABASE_KEY')
} 