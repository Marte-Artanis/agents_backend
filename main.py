from fastapi import FastAPI
from pydantic import BaseModel
from agents_structures import generate_character_response, AgentMemory

app = FastAPI()

class ChatRequest(BaseModel):
    character: str
    prompt: str
    historical_period: str
    historical_factors: str
    language: str

@app.post("/chat/")
async def chat(request: ChatRequest):
    # Criar/carregar memória do personagem direto do arquivo .faiss
    memory = AgentMemory(request.character)

    response = generate_character_response(
        character=request.character,
        user_input=request.prompt,
        historical_period=request.historical_period,
        historical_factor=request.historical_factors,
        language=request.language,
        memory=memory
    )
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 