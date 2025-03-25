import os
from pathlib import Path
from database import db

def get_migration_files():
    """Retorna lista de arquivos de migration ordenados"""
    migrations_dir = Path(__file__).parent / 'migrations'
    files = []
    
    for file in migrations_dir.glob('*.sql'):
        if file.name.startswith('0'):
            continue  # Pula o arquivo de controle (000_migrations.sql)
        files.append(file)
    
    return sorted(files)

def get_applied_migrations():
    """Retorna lista de migrations já aplicadas"""
    try:
        return [row['version'] for row in db.fetch("SELECT version FROM migrations ORDER BY id")]
    except:
        return []

def apply_migration(file_path):
    """Aplica uma migration específica"""
    print(f"Aplicando migration: {file_path.name}")
    
    # Lê o conteúdo do arquivo
    with open(file_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Executa as queries
    db.execute(sql)
    
    # Registra a migration
    version = file_path.stem  # Nome do arquivo sem extensão
    db.execute(
        "INSERT INTO migrations (version) VALUES (%s)",
        [version]
    )

def run_migrations():
    """Executa todas as migrations pendentes"""
    print("Iniciando migrations...")
    
    # Primeiro, cria a tabela de controle se não existir
    control_file = Path(__file__).parent / 'migrations' / '000_migrations.sql'
    with open(control_file, 'r', encoding='utf-8') as f:
        db.execute(f.read())
    
    # Pega as migrations já aplicadas
    applied = get_applied_migrations()
    print(f"Migrations já aplicadas: {len(applied)}")
    
    # Pega todas as migrations disponíveis
    available = get_migration_files()
    print(f"Migrations disponíveis: {len(available)}")
    
    # Aplica as migrations pendentes
    for file_path in available:
        version = file_path.stem
        if version not in applied:
            try:
                apply_migration(file_path)
                print(f"Migration {version} aplicada com sucesso!")
            except Exception as e:
                print(f"Erro ao aplicar migration {version}: {e}")
                raise
    
    print("Migrations concluídas!")

if __name__ == "__main__":
    run_migrations() 