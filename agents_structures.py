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

def generate_character_response(
    character: str,
    prompt: str,
    historical_period: str,
    historical_factor: str,
    language: str,
    memory: AgentMemory = None
) -> str:
    """Gera uma resposta do personagem baseada no prompt e contexto"""
    try:
        # Obter descrições e prompts
        character_desc = character_descriptions_prompts.get(character, "")
        period_desc = available_periods_prompts.get(historical_period, "")
        factor_desc = character_historical_factors_prompts.get(historical_factor, "")
        language_desc = language_descriptions_prompts.get(language, "")

        # Construir contexto histórico
        context = f"Período: {historical_period}, Fator Histórico: {historical_factor}"
        
        # Recuperar histórico relevante
        memory_context = ""
        if memory:
            try:
                # Buscar memórias semanticamente relevantes para o prompt atual
                prompt_memories = memory.get_relevant_memories(prompt, k=3)
                
                # Buscar memórias semanticamente relevantes para o contexto
                context_memories = memory.get_relevant_memories(context, k=2)
                
                # Combinar e remover duplicatas (verificando conteúdo, não apenas referência)
                deduplicated_memories = []
                content_hashes = set()
                
                for mem in prompt_memories + context_memories:
                    # Criar um hash simplificado do conteúdo para identificar similaridade
                    content_parts = mem.lower().split("usuário disse:")
                    if len(content_parts) > 1:
                        response_part = content_parts[1].split(f"{character} respondeu:")[1] if len(content_parts[1].split(f"{character} respondeu:")) > 1 else ""
                        content_hash = response_part.strip()[:50]  # primeiros 50 caracteres da resposta
                        
                        # Se esse conteúdo ou algo muito similar já foi incluído, pule
                        if content_hash not in content_hashes:
                            content_hashes.add(content_hash)
                            deduplicated_memories.append(mem)
                
                # Limitar a 3 memórias no máximo para não sobrecarregar
                final_memories = deduplicated_memories[:3]
                
                # Formatar as memórias para o contexto
                if final_memories:
                    memory_context = "Histórico relevante da conversa (apenas como referência):\n" + "\n---\n".join(final_memories)
            except Exception as mem_error:
                print(f"Erro ao recuperar memórias: {str(mem_error)}")
                memory_context = "Sem histórico de conversa disponível."

        # Criar prompt do sistema com equilíbrio entre contexto e foco na mensagem atual
        system_prompt = f"""Você é {character}.

        Contexto do personagem:
        {character_desc}

        Período histórico:
        {period_desc}

        Fatores históricos:
        {factor_desc}

        Idioma e estilo:
        {language_desc}

        {memory_context}

        INSTRUÇÕES IMPORTANTES PARA RESPONDER:
        1. Mantenha-se fiel ao personagem e período histórico
        2. Use o idioma e estilo especificados
        3. NUNCA repita exatamente a mesma resposta que você já deu antes
        4. RESPONDA à mensagem atual do usuário: "{prompt}"
        5. Use o histórico apenas como contexto secundário
        6. Priorize a resposta à mensagem atual, não ao histórico
        7. Varie suas respostas, mesmo para perguntas similares
        8. Quando o usuário fizer perguntas simples ou saudações, dê respostas diretas mas VARIADAS
        9. Mantenha suas respostas relevantes para o que o usuário acabou de perguntar
        10. É PROIBIDO repetir o mesmo padrão de resposta de interações anteriores
        11. Seja criativo e original em cada resposta
        12. NUNCA use aspas em suas respostas - isso é MUITO importante
        """

        # Criar a cadeia de mensagens
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]

        # Gerar resposta
        response = chat(messages)
        
        # Armazenar na memória se existir
        if memory:
            memory.add_memory(prompt, response.content, context)
        
        return response.content

    except Exception as e:
        print(f"Erro ao recuperar memórias: {str(e)}")
        raise Exception(f"Erro ao gerar resposta: {str(e)}")

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