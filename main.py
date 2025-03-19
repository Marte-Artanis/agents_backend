from fastapi import FastAPI
from pydantic import BaseModel
from agents_structures import groq_api_call, AgentMemory

app = FastAPI()

class ChatRequest(BaseModel):
    personagem: str
    prompt: str
    periodo_historico: str
    fatores_historicos: str
    idioma: str

@app.post("/chat/")
async def chat(request: ChatRequest):
    # Criar/carregar memória do personagem direto do arquivo .faiss
    memory = AgentMemory(request.personagem)

    resposta = groq_api_call(
        request.personagem,
        request.prompt,
        request.periodo_historico,
        request.fatores_historicos,
        request.idioma,
        memory=memory
    )
    return {"resposta": resposta}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 