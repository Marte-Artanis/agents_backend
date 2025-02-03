from fastapi import FastAPI
from pydantic import BaseModel
from tests_agents.agente_da_terra_media_1 import groq_api_call  # Importa a função do seu arquivo

app = FastAPI()

class ChatRequest(BaseModel):
    personagem: str
    prompt: str
    periodo_historico: str
    fatores_historicos: str  # Aceita apenas uma string
    idioma: str

@app.post("/chat/")
async def chat(request: ChatRequest):
    resposta = groq_api_call(
        request.personagem,
        request.prompt,
        request.periodo_historico,
        request.fatores_historicos,
        request.idioma
    )
    return {"resposta": resposta}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)