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
from session_manager import SessionManager

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

# Inicializar gerenciador de sessões
session_manager = SessionManager()

class AgentMemory:
    def __init__(self, character_name: str, session_id: str, user_id: int):
        self.character_name = character_name
        self.session_id = session_id
        self.user_id = user_id
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en-v1.5"
        )
        self.index = pc.Index("character-memories")
    
    def add_memory(self, user_input: str, response: str, context: str):
        print("\n=== SALVANDO NO PINECONE ===")
        print(f"User ID: {self.user_id}")
        print(f"Character: {self.character_name}")
        print(f"Session ID: {self.session_id}")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Adicionar ao Pinecone para busca semântica e histórico
        memory_text = f"{user_input} {response}"
        vector = self.embeddings.embed_query(memory_text)
        
        vector_id = f"{self.user_id}_{self.session_id}_{self.character_name}_{timestamp}"
        namespace = f"{self.user_id}_{self.character_name}"
        
        print(f"Vector ID: {vector_id}")
        print(f"Namespace: {namespace}")
        
        metadata = {
            'timestamp': timestamp,
            'period': context.split(',')[0].replace('Período:', '').strip(),
            'character': self.character_name,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'input': user_input,
            'response': response,
            'full_context': context
        }
        print(f"Metadata: {metadata}")
        
        try:
            print("\nTentando salvar no Pinecone...")
            self.index.upsert(
                vectors=[{
                    'id': vector_id,
                    'values': vector,
                    'metadata': metadata
                }],
                namespace=namespace
            )
            print("✅ Salvo com sucesso no Pinecone!")
        except Exception as e:
            print(f"❌ Erro ao salvar no Pinecone: {str(e)}")
            raise e
        
        print("=== FIM DO SALVAMENTO ===\n")
    
    def get_relevant_memories(self, current_context: str, k: int = 5) -> List[str]:
        print("\n=== BUSCANDO MEMÓRIAS ===")
        print(f"User ID: {self.user_id}")
        print(f"Character: {self.character_name}")
        print(f"Contexto: {current_context[:100]}...")
        
        query_vector = self.embeddings.embed_query(current_context)
        namespace = f"{self.user_id}_{self.character_name}"
        print(f"Namespace: {namespace}")
        
        try:
            results = self.index.query(
                vector=query_vector,
                top_k=k,
                namespace=namespace,
                include_metadata=True
            )
            print(f"✅ Encontradas {len(results.matches)} memórias")
            for i, match in enumerate(results.matches, 1):
                print(f"\nMemória {i}:")
                print(f"Score: {match.score}")
                print(f"User ID: {match.metadata.get('user_id')}")
                print(f"Timestamp: {match.metadata.get('timestamp')}")
        except Exception as e:
            print(f"❌ Erro ao buscar memórias: {str(e)}")
            return []
        
        print("=== FIM DA BUSCA ===\n")
        
        memories = []
        for match in results.matches:
            metadata = match.metadata
            period = metadata.get('period', "Período desconhecido")
            user_input = metadata.get('input', 'Input desconhecido')
            response = metadata.get('response', 'Resposta desconhecida')
            
            memory_text = f"""[{period}]
            Usuário disse: {user_input}
            {self.character_name} respondeu: {response}"""
            memories.append(memory_text)
        
        return memories
    
    def get_chat_history(self) -> List[Dict]:
        """Recupera histórico completo da conversa do Pinecone"""
        results = self.index.query(
            vector=[0] * 1024,  # vetor dummy para pegar todos
            top_k=100,  # ajuste conforme necessário
            namespace=f"{self.user_id}_{self.character_name}",
            include_metadata=True
        )
        
        messages = []
        for match in results.matches:
            metadata = match.metadata
            messages.extend([
                {"role": "user", "content": metadata['input']},
                {"role": "assistant", "content": metadata['response']}
            ])
        
        # Ordenar por timestamp
        messages.sort(key=lambda x: x.get('timestamp', ''))
        return messages

def generate_character_response(character: str, user_input: str, historical_period: str, historical_factor: str, language: str, memory: AgentMemory = None):
    character_description = character_descriptions_prompts.get(character, "Você é um personagem desconhecido, sem uma descrição definida.")
    language_description = language_descriptions_prompts.get(language, "Descrição do idioma não encontrada.")

    # Buscar memórias relevantes do Pinecone
    if memory:
        input_memories = memory.get_relevant_memories(user_input, k=3)
        context_memories = memory.get_relevant_memories(f"{historical_period} {historical_factor}", k=2)
        
        all_memories = []
        seen = set()
        
        for mem in input_memories + context_memories:
            if mem not in seen:
                all_memories.append(mem)
                seen.add(mem)
        
        memories_text = "\n".join(all_memories) if all_memories else "Sem memórias anteriores relevantes."
    else:
        memories_text = "Sem memórias anteriores."

    # Construir mensagem do sistema
    system_message_content = f"""
    Você é {character}, ou seja, {character_description}.
    
    PERGUNTA ATUAL DO USUÁRIO: "{user_input}"
    Esta é a pergunta que você DEVE responder.
    
    Contexto atual:
    - **Período**: {historical_period}
    - **Situação**: {historical_factor}
    - **Idioma**: {language} ({language_description})

    Memórias relevantes da conversa:
    {memories_text}

    REGRAS ESSENCIAIS:
    1. NUNCA use aspas em suas respostas - isso é MUITO importante
    2. NUNCA diga que é uma IA ou que está interpretando um papel
    3. NUNCA faça referências meta à conversa (como em nossa conversa anterior)
    4. NUNCA use linguagem ou referências que seriam anacrônicas para seu personagem e período

    DIRETRIZES DE PERSONALIDADE:
    1. Responda como se você realmente fosse o personagem
    2. Use o vocabulário e maneirismos típicos do seu personagem e período histórico
    3. Mantenha suas emoções, opiniões e personalidade consistentes
    4. Reaja naturalmente às interações do usuário como seu personagem reagiria
    5. Use o idioma {language} quando fizer sentido no contexto
    6. Suas respostas podem ser longas ou curtas, dependendo do que fizer mais sentido
    7. Use qualquer estilo de pontuação, ênfase ou expressão que combine com sua personalidade

    LEMBRE-SE:
    1. Use as memórias anteriores para manter consistência, mas não as mencione explicitamente
    2. Mantenha-se fiel ao seu personagem em todas as interações
    3. Responda de forma natural e apropriada ao contexto da conversa
    """

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
    memory = AgentMemory(selected_character, "session1", 1)

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