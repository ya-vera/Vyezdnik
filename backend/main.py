from fastapi import FastAPI
from pydantic import BaseModel
from app.agents.orchestrator import orchestrator
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str
    country: str

@app.post("/chat")
def chat(req: ChatRequest):
    answer = orchestrator(req.message, req.country.lower())
    return {"answer": answer}