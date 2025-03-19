import os
import hashlib
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from datetime import datetime
from prompts.character_descriptions import character_descriptions_prompts
from prompts.language_descriptions import language_descriptions_prompts
from prompts.available_periods import available_periods_prompts
from prompts.character_historical_factors import character_historical_factors_prompts

load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')

# Configure chat
chat = ChatGroq(
    temperature=0,
    model_name="mixtral-8x7b-32768",  
    groq_api_key=groq_api_key
)

class AgentMemory:
    def __init__(self, character_name):
        self.character_name = character_name
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.memory_file = f"memories_{character_name}.faiss"
        
        # Tentar carregar memória existente ou criar nova
        if os.path.exists(self.memory_file):
            self.vector_store = FAISS.load_local(self.memory_file, self.embeddings)
        else:
            self.vector_store = FAISS.from_texts(["Início da memória"], self.embeddings)
    
    def add_memory(self, user_input, response, context):
        # Criar uma entrada de memória estruturada
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        memory_entry = f"""
        Tempo: {timestamp}
        Contexto: {context}
        Usuário: {user_input}
        Resposta: {response}
        """
        
        # Adicionar à memória vetorial
        self.vector_store.add_texts([memory_entry])
        
        # Salvar no disco
        self.vector_store.save_local(self.memory_file)
    
    def get_relevant_memories(self, current_context, k=3):
        # Buscar memórias relevantes
        memories = self.vector_store.similarity_search(current_context, k=k)
        return [mem.page_content for mem in memories]

def groq_api_call(character, user_input, historical_period, historical_factor, language, memory=None):
    character_description = character_descriptions_prompts.get(character, "Você é um personagem desconhecido, sem uma descrição definida.")
    language_description = language_descriptions_prompts.get(language, "Descrição do idioma não encontrada.")

    # Buscar memórias relevantes se existirem
    relevant_memories = []
    if memory:
        current_context = f"{user_input} {historical_period} {historical_factor}"
        relevant_memories = memory.get_relevant_memories(current_context)
        memories_text = "\n".join(relevant_memories)
    else:
        memories_text = "Sem memórias anteriores."

    # Build system message
    system_message_content = f"""
    Você é {character}, ou seja, {character_description}.
    O contexto histórico é o seguinte:
    - **Período Histórico**: {historical_period}
    - **Fator Histórico**: {historical_factor}
    - **Idioma**: {language} ({language_description})

    Memórias relevantes da sua história:
    {memories_text}

    Use SEMPRE tantas palavras quanto possíveis do idioma escolhido em suas respostas.
    Você está falando com o usuário, que disse {user_input}. Aja como {character} e responda SEMPRE na sua voz e estilo característicos, nunca se limitando apenas aos exemplos de palavras expostas. 
    Foque SOMENTE na fala do personagem, e NUNCA inclua traduções, explicações ou formatações adicionais.
    """

    # Configure chat template with dynamic data
    chat_template = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_message_content),
        HumanMessage(content=user_input),
        AIMessage(content=f"{character}, com sua voz característica, e no idioma {language}, começa a responder...")
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
        response = groq_api_call(
            selected_character, 
            user_input, 
            selected_period, 
            selected_factor, 
            selected_language,
            memory=memory
        )
        print(response)

if __name__ == "__main__":
    main()