from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents_structures import generate_character_response, AgentMemory
from prompts.available_periods import available_periods_prompts
from prompts.character_descriptions import character_descriptions_prompts
from prompts.character_historical_factors import character_historical_factors_prompts
from prompts.language_descriptions import language_descriptions_prompts

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    character: str
    prompt: str
    historical_period: str
    historical_factors: str
    language: str

@app.get("/characters")
async def get_characters():
    characters = {}
    for char_name, description in character_descriptions_prompts.items():
        characters[char_name] = {
            "name": char_name,
            "description": description.split("\n")[0].strip()  # Pega apenas a primeira linha da descrição
        }
    return characters

@app.get("/historical-periods/{character}")
async def get_historical_periods(character: str):
    if character in available_periods_prompts:
        return available_periods_prompts[character]
    return []

@app.get("/historical-factors/{character}")
async def get_historical_factors(character: str):
    if character in character_historical_factors_prompts:
        return character_historical_factors_prompts[character]
    return []

@app.get("/languages")
async def get_languages():
    return language_descriptions_prompts

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