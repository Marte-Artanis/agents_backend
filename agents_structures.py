import os
from typing import List, Dict
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_community.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec
from datetime import datetime
from prompts.character_descriptions import character_descriptions_prompts
from prompts.language_descriptions import language_descriptions_prompts
from prompts.available_periods import available_periods_prompts
from prompts.character_historical_factors import character_historical_factors_prompts

load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')
pinecone_api_key = os.getenv('PINECONE_API_KEY')

# Initialize Pinecone
pc = Pinecone(api_key=pinecone_api_key)

# Create index if it doesn't exist
if 'character-memories' not in pc.list_indexes().names():
    pc.create_index(
        name='character-memories',
        dimension=1024,  # Dimensão do modelo BAAI/bge-large-en-v1.5
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-west-2'
        )
    )

# Configure chat
chat = ChatGroq(
    temperature=0,
    model_name="llama3-8b-8192",  
    groq_api_key=groq_api_key
)

class AgentMemory:
    def __init__(self, character_name: str):
        self.character_name = character_name
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en-v1.5"  # Modelo que gera embeddings de 1024 dimensões
        )
        self.index = pc.Index("character-memories")
    
    def add_memory(self, user_input, response, context):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Criar texto para embedding que capture a semântica da interação
        memory_text = f"{user_input} {response}"
        
        # Gerar embedding do texto
        vector = self.embeddings.embed_query(memory_text)
        
        # Adicionar à memória vetorial com metadados estruturados
        self.index.upsert(
            vectors=[{
                'id': f"{self.character_name}_{timestamp}",
                'values': vector,
                'metadata': {
                    'timestamp': timestamp,
                    'period': context.split(',')[0].replace('Período:', '').strip(),
                    'character': self.character_name,
                    'input': user_input,
                    'response': response,
                    'full_context': context
                }
            }],
            namespace=self.character_name
        )
    
    def get_relevant_memories(self, current_context, k=5):
        # Buscar usando apenas o input do usuário para melhor correspondência
        query_vector = self.embeddings.embed_query(current_context)
        
        # Buscar memórias relevantes
        results = self.index.query(
            vector=query_vector,
            top_k=k,
            namespace=self.character_name,
            include_metadata=True
        )
        
        memories = []
        for match in results.matches:
            metadata = match.metadata
            
            # Tentar extrair o período do contexto se não existir diretamente
            period = metadata.get('period')
            if not period and 'full_context' in metadata:
                period = metadata['full_context'].split(',')[0].replace('Período:', '').strip()
            elif not period and 'context' in metadata:
                period = metadata['context'].split(',')[0].replace('Período:', '').strip()
            else:
                period = "Período desconhecido"
            
            # Pegar input/response com fallback para campos antigos
            user_input = metadata.get('input') or metadata.get('user_input', 'Input desconhecido')
            response = metadata.get('response', 'Resposta desconhecida')
            
            memory_text = f"""[{period}]
            Usuário disse: {user_input}
            {self.character_name} respondeu: {response}"""
            memories.append(memory_text)
        
        return memories

def generate_character_response(character, user_input, historical_period, historical_factor, language, memory=None):
    character_description = character_descriptions_prompts.get(character, "Você é um personagem desconhecido, sem uma descrição definida.")
    language_description = language_descriptions_prompts.get(language, "Descrição do idioma não encontrada.")

    # Buscar memórias relevantes se existirem
    if memory:
        input_memories = memory.get_relevant_memories(user_input, k=3)
        context_memories = memory.get_relevant_memories(f"{historical_period} {historical_factor}", k=2)
        
        # Combinar as memórias, removendo duplicatas
        all_memories = []
        seen = set()
        
        for mem in input_memories + context_memories:
            if mem not in seen:
                all_memories.append(mem)
                seen.add(mem)
        
        memories_text = "\n".join(all_memories) if all_memories else "Sem memórias anteriores relevantes."
    else:
        memories_text = "Sem memórias anteriores."

    # Build system message
    system_message_content = f"""
    Você é {character}, ou seja, {character_description}.
    
    PERGUNTA ATUAL DO USUÁRIO: "{user_input}"
    Esta é a pergunta que você DEVE responder diretamente.
    
    Contexto atual:
    - **Período**: {historical_period}
    - **Situação**: {historical_factor}
    - **Idioma**: {language} ({language_description})

    Memórias da conversa:
    {memories_text}

    Instruções importantes:
    1. Responda DIRETAMENTE à pergunta atual do usuário
    2. Use as memórias para dar contexto e evitar repetições
    3. Mantenha sua personalidade, mas seja natural
    4. Use o idioma {language} quando fizer sentido
    5. Evite repetir frases ou metáforas que você já usou antes
    6. Não ignore a pergunta atual para falar de outros assuntos

    Lembre-se: Seja direto, natural e evite repetir o que já disse antes.
    """

    # Configure chat template with dynamic data
    chat_template = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_message_content),
        HumanMessage(content=user_input)
    ])

    formatted_prompt = chat_template.format_messages()
    model_response = chat.invoke(formatted_prompt)
    response = model_response.content.strip()

    # Armazenar na memória se existir
    if memory:
        context = f"Período: {historical_period}, Fator: {historical_factor}"
        memory.add_memory(user_input, response, context)

    return response

def main():
    # Fixed test configuration
    selected_character = "Saruman"
    selected_language = "Westron"
    selected_period = "A traição de Saruman"
    selected_factor = "A busca por poder"

    # Inicializar memória do personagem
    memory = AgentMemory(selected_character)

    print("\nTest configuration:")
    print(f"Character: {selected_character}")
    print(f"Language: {selected_language}")
    print(f"Historical Period: {selected_period}")
    print(f"Historical Factor: {selected_factor}")

    # User interaction
    print("\nType 'exit' to quit.")
    while True:
        user_input = input("\nAsk your question or type 'exit': ")
        if user_input.lower() == 'exit':
            break
        
        # Get response with memory
        response = generate_character_response(
            selected_character, 
            user_input, 
            selected_period, 
            selected_factor, 
            selected_language,
            memory=memory
        )
        print(f"\n{response}")

if __name__ == "__main__":
    main()