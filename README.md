# Project Infinity - Backend

Backend da aplicação que permite interações com personagens do universo Tolkien através de LLMs (Large Language Models), gerando respostas contextualizadas baseadas em períodos históricos e fatores específicos.

## Tecnologias

- Python 3.10+
- FastAPI
- Groq
- Langchain
- Pinecone
- Alembic (Gerenciamento de Migrações)

## Configuração

1. Crie e ative um ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

4. Execute as migrações do banco de dados:
```bash
python run_migrations.py
```

5. Inicie o servidor:
```bash
uvicorn main:app --reload --port 8001
```

O backend estará disponível em `http://localhost:8001`

## Gerenciamento de Migrações

O projeto usa Alembic para gerenciar as migrações do banco de dados. Aqui estão os comandos principais:

### Criar uma nova migração
```bash
python create_migration.py "descrição da migração"
```

### Executar migrações pendentes
```bash
python run_migrations.py
```

### Reverter a última migração
```bash
alembic downgrade -1
```

### Ver status das migrações
```bash
alembic current
alembic history
```

## Funcionalidades

- Geração de respostas contextualizadas usando Claude
- Suporte a múltiplos personagens (Ungoliant, Sauron, Azog, Saruman, Gollum)
- Contextualização baseada em períodos históricos
- Adaptação de respostas baseada em fatores históricos
- Suporte a múltiplos idiomas (Westron, Sindarin, Língua dos Orcs, Quenya)

## Estrutura do Projeto

- `/prompts` - Definições de prompts e características dos personagens
  - `available_periods.py` - Períodos históricos disponíveis
  - `character_descriptions.py` - Descrições e personalidades
  - `character_historical_factors.py` - Fatores históricos
  - `language_descriptions.py` - Descrições e exemplos de idiomas
- `/migrations` - Arquivos de migração do banco de dados
  - `/versions` - Versões individuais das migrações
- `agents_structures.py` - Estruturas principais dos agentes
- `main.py` - Endpoints da API FastAPI
- `database.py` - Configuração e conexão com o banco de dados
- `alembic.ini` - Configuração do Alembic

## API Endpoints

- `GET /characters` - Lista todos os personagens disponíveis
- `GET /historical-periods/{character}` - Retorna períodos históricos do personagem
- `GET /historical-factors/{character}` - Retorna fatores históricos do personagem
- `GET /languages` - Lista todos os idiomas disponíveis
- `POST /chat` - Endpoint principal para interação com os personagens
