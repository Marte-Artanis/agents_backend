import os
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
    
    # Obter a descrição do idioma
    idioma_descricao = idiomas_descricao_prompts.get(idioma, "Descrição do idioma não encontrada.")

    # Montar a mensagem do sistema
    system_message_content = f"""
    Você é {personagem}, ou seja, {personagem_descricao}.
    O contexto histórico é o seguinte:
    - **Período Histórico**: {periodo_historico}
    - **Fator Histórico**: {fator_historico}  # Agora lidando com um único fator
    - **Idioma**: {idioma} ({idioma_descricao}). Use SEMPRE tantas palavras quanto possíveis do idioma escolhido em suas respostas.
    Você está falando com o usuário, que disse {user_input}. Aja como {personagem} e responda SEMPRE na sua voz e estilo característicos, nunca se limitando apenas aos exemplos de palavras expostas. 
    Foque SOMENTE na fala do personagem, e NUNCA inclua traduções, explicações ou formatações adicionais.
    """

    # Configuração do prompt para o modelo com os dados dinâmicos
    chat_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_message_content),
            HumanMessage(content=user_input),  # Aqui é user_input
            AIMessage(content=f"{personagem}, com sua voz característica, e no idioma {idioma}, começa a responder...")
        ]
    )

    formatted_prompt = chat_template.format_messages()
    print(formatted_prompt)

    response = chat.invoke(formatted_prompt) 
    resposta = response.content.strip()  # Remove espaços em branco e quebras de linha

    return resposta  # Retorna a resposta diretamente

def main():
    print("Agente da Terra-média - Escolha seu Personagem, Idioma e Fatores Históricos")
    
    # Listar todos os personagens disponíveis
    print("Personagens disponíveis:")
    for personagem in personagens_descricao.keys():
        print(f"- {personagem}")

    personagem_escolhido = input("Digite o nome do personagem: ").strip()

    # Verificar se o personagem escolhido existe
    if personagem_escolhido not in personagens_descricao:
        print("Personagem não encontrado. Tente novamente.")
        return

    # Listar idiomas disponíveis
    print("\nIdiomas disponíveis:")
    for idioma in idiomas_descricao.keys():
        print(f"- {idioma}")

    idioma_escolhido = input("Digite o nome do idioma: ").strip()

    # Verificar se o idioma escolhido existe
    if idioma_escolhido not in idiomas_descricao:
        print("Idioma não encontrado. Tente novamente.")
        return

    # Listar períodos históricos disponíveis para o personagem escolhido
    periodos_historicos = periodos_disponiveis[personagem_escolhido]
    print(f"\nPeríodos históricos disponíveis para {personagem_escolhido}:")
    for i, periodo in enumerate(periodos_historicos, start=1):
        print(f"{i}. {periodo}")

    periodo_escolhido = input("Escolha um período histórico pelo número ou nome: ")

    # Verificar se o período escolhido é válido
    if periodo_escolhido.isdigit():
        periodo_index = int(periodo_escolhido) - 1
        if not (0 <= periodo_index < len(periodos_historicos)):
            print("Período não encontrado. Tente novamente.")
            return
        periodo_historico_escolhido = periodos_historicos[periodo_index]  # Pega o período como string
    else:
        if periodo_escolhido not in periodos_historicos:
            print("Período não encontrado. Tente novamente.")
            return
        periodo_historico_escolhido = periodo_escolhido  # Pega o período como string

    # Listar fatores históricos disponíveis para o personagem escolhido
    fatores_historicos = fatores_historicos_por_personagem[personagem_escolhido]
    print(f"\nFatores históricos disponíveis para {personagem_escolhido}:")
    for i, fator in enumerate(fatores_historicos, start=1):
        print(f"{i}. {fator}")

    fator_escolhido = input("Escolha um fator histórico pelo número ou nome: ")

    # Verificar se o fator escolhido é válido
    if fator_escolhido.isdigit():
        fator_index = int(fator_escolhido) - 1
        if not (0 <= fator_index < len(fatores_historicos)):
            print("Fator histórico não encontrado. Tente novamente.")
            return
        fatores_historicos_escolhido = fatores_historicos[fator_index]  # Pega o fator como string
    else:
        if fator_escolhido not in fatores_historicos:
            print("Fator histórico não encontrado. Tente novamente.")
            return
        fatores_historicos_escolhido = fator_escolhido  # Pega o fator como string

    # Exibir a escolha final de forma concisa
    print(f"\nVocê escolheu:")
    print(f"Personagem: {personagem_escolhido}")
    print(f"Idioma: {idioma_escolhido}")
    print(f"Período Histórico: {periodo_historico_escolhido}")  # Usar a variável correta
    print(f"Fator Histórico: {fatores_historicos_escolhido}")

    # Interação com o usuário
    print("\nDigite 'sair' para encerrar.")
    while True:
        user_input = input("Faça sua pergunta ou digite 'sair': ")
        if user_input.lower() == 'sair':
            break
        
        # Chamar a função para obter a resposta
        resposta = groq_api_call(personagem_escolhido, user_input, periodo_historico_escolhido, fatores_historicos_escolhido, idioma_escolhido)
        print(resposta)  # Exibir a resposta diretamente

if __name__ == "__main__":
    main()