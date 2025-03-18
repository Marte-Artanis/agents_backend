import os
import hashlib
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from prompts.personagens_descricao import personagens_descricao_prompts
from prompts.idiomas_descricao import idiomas_descricao_prompts
from prompts.periodos_disponiveis import periodos_disponiveis_prompts
from prompts.fatores_historicos_por_personagem import fatores_historicos_por_personagem_prompts

load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')

chat = ChatGroq(
    temperature=0,
    model_name="mixtral-8x7b-32768",  
    groq_api_key=groq_api_key
)

personagens_descricao = personagens_descricao_prompts
idiomas_descricao = idiomas_descricao_prompts
periodos_disponiveis = periodos_disponiveis_prompts
fatores_historicos_por_personagem = fatores_historicos_por_personagem_prompts

def groq_api_call(personagem, user_input, periodo_historico, fator_historico, idioma):
    personagem_descricao = personagens_descricao.get(personagem, "Você é um personagem desconhecido, sem uma descrição definida.")
    
    idioma_descricao = idiomas_descricao_prompts.get(idioma, "Descrição do idioma não encontrada.")

    # Montar a mensagem do sistema
    system_message_content = f"""
    Você é {personagem}, ou seja, {personagem_descricao}.
    O contexto histórico é o seguinte:
    - **Período Histórico**: {periodo_historico}
    - **Fator Histórico**: {fator_historico}
    - **Idioma**: {idioma} ({idioma_descricao}). Use SEMPRE tantas palavras quanto possíveis do idioma escolhido em suas respostas.
    Você está falando com o usuário. Aja como {personagem} e responda SEMPRE na sua voz e estilo característicos, nunca se limitando apenas aos exemplos de palavras expostas. 
    Foque SOMENTE na fala do personagem, e NUNCA inclua traduções, explicações ou formatações adicionais.
    """

    # Criar o template do chat
    chat_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_message_content),
            HumanMessage(content=user_input),
            AIMessage(content=f"{personagem}, com sua voz característica, começa a responder...")
        ]
    )

    # Formatar o prompt
    messages = chat_template.format_messages()

    # Usar o chat para gerar a resposta
    response = chat(messages)
    return response.content.strip()

def main():
    personagem_escolhido = "Sauron"
    idioma_escolhido = "Língua dos Orcs"
    periodo_historico_escolhido = "A criação do Um Anel"
    fatores_historicos_escolhido = "A busca pelo Um Anel"

    print(f"\nConfiguração de teste:")
    print(f"Personagem: {personagem_escolhido}")
    print(f"Idioma: {idioma_escolhido}")
    print(f"Período Histórico: {periodo_historico_escolhido}")
    print(f"Fator Histórico: {fatores_historicos_escolhido}")

    # Interação com o usuário
    print("\nDigite 'sair' para encerrar.")
    while True:
        user_input = input("\nFaça sua pergunta ou digite 'sair': ")
        if user_input.lower() == 'sair':
            break
        
        # Chamar a função para obter a resposta
        resposta = groq_api_call(personagem_escolhido, user_input, periodo_historico_escolhido, fatores_historicos_escolhido, idioma_escolhido)
        print(resposta)  # Exibir a resposta diretamente

if __name__ == "__main__":
    main() 
