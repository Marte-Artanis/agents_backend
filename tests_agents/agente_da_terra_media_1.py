import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage  
load_dotenv()

groq_api_key = os.getenv('GROQ_API_KEY')

chat = ChatGroq(
    temperature=0,
    model_name="mixtral-8x7b-32768",  
    groq_api_key=groq_api_key 
)

personagens_descricao = {
    "Ungoliant": "Uma criatura antiga e poderosa, conhecida por sua forma de aranha. Insaciável e traiçoeira.",
    "Sauron": "O Senhor do Escuro, manipulador e astuto, sempre tramando para alcançar seus objetivos.",
    "Azog": "Azog, o Deflorador de Anões, brutal e astuto, conhecido por sua ferocidade em batalha.",
    "Saruman": "Um mago que se voltou para o lado do mal, calculista e ambicioso.",
    "Gollum": "Uma criatura corrompida pelo Um Anel, astuto e traiçoeiro, dividido entre sua natureza maligna e sua antiga identidade."
}

idiomas_descricao = {
    "Westron": "A língua comum entre os povos da Terra-média. Exemplos: 'mellon' (amigo), 'loth' (flor).",
    "Sindarin": "Língua élfica, rica em poesia. Exemplos: 'na vedui' (finalmente), 'athrad' (coragem).",
    "Língua dos Orcs": "Uma língua grosseira e áspera. Exemplos: 'durbat' (matar), 'gûl' (mestre).",
    "Quenya": "Uma língua élfica antiga. Exemplos: 'yéni' (anos), 'anda' (norte)."
}

periodos_disponiveis = {
    "Ungoliant": ["A origem de Ungoliant", "A devoração da luz", "A aliança com Morgoth"],
    "Sauron": ["A criação do Um Anel", "A Guerra do Anel", "A manipulação dos povos da Terra-média"],
    "Azog": ["A ascensão de Azog à liderança dos Orcs", "A Batalha dos Cinco Exércitos"],
    "Saruman": ["A traição de Saruman", "A busca por poder"],
    "Gollum": ["A busca pelo Um Anel", "A luta interna entre Sméagol e Gollum"]
}

fatores_historicos_por_personagem = {
    "Ungoliant": ["A devoração da luz", "A aliança com Morgoth"],
    "Sauron": ["A busca pelo Um Anel", "A manipulação dos povos da Terra-média"],
    "Azog": ["A formação da legião de Azog", "A derrota dos Anões em Moria"],
    "Saruman": ["A traição de Saruman", "A busca por poder"],
    "Gollum": ["A corrupção pelo Um Anel", "A luta interna entre Sméagol e Gollum"]
}

def groq_api_call(personagem, prompt, periodo_historico, fatores_historicos, idioma):
    personagem_descricao = personagens_descricao.get(personagem, "Você é um personagem desconhecido, sem uma descrição definida.")
    
    system_message_content = f"""
    Você é {personagem}, ou seja, {personagem_descricao}.
    O contexto histórico é o seguinte:
    - **Período Histórico**: {periodo_historico}
    - **Fatores Históricos**: {fatores_historicos}
    - **Idioma**: {idioma}. 
    Responda como se fosse o personagem, usando sua voz e estilo característicos. Não inclua traduções, explicações ou formatações adicionais. Apenas a fala do personagem.
    """

    # Configuração do prompt para o modelo com os dados dinâmicos
    chat_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_message_content),
            HumanMessage(content=prompt),
            AIMessage(content=f"{personagem}, com sua voz característica, começa a responder...")
        ]
    )

    formatted_prompt = chat_template.format_messages()

    response = chat.invoke(formatted_prompt) 
    resposta = response.content.strip()  # Remove espaços em branco e quebras de linha

    # Adicione um print para verificar a resposta
    print("Resposta do modelo:", resposta)  # Verifique o que está sendo retornado

    return resposta

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
    else:
        if periodo_escolhido not in periodos_historicos:
            print("Período não encontrado. Tente novamente.")
            return

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
    print(f"Período Histórico: {periodos_historicos[int(periodo_escolhido) - 1]}")
    print(f"Fator Histórico: {fatores_historicos_escolhido}")

    # Interação com o usuário
    print("\nDigite 'sair' para encerrar.")
    while True:
        user_input = input("Faça sua pergunta ou digite 'sair': ")
        if user_input.lower() == 'sair':
            break
        
        # Chamar a função para obter a resposta
        resposta = groq_api_call(personagem_escolhido, user_input, periodos_historicos[int(periodo_escolhido) - 1], fatores_historicos_escolhido, idioma_escolhido)
        print(resposta)  # Exibir a resposta diretamente

if __name__ == "__main__":
    main()