from fastapi import APIRouter, HTTPException
from ..schemas.llm import LLMRequest, LLMResponse
import os
import requests

try:
    import ollama
except ImportError:
    ollama = None

router = APIRouter(tags=["LLM"])

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OPEN_INTERPRETER_URL = os.getenv("OPEN_INTERPRETER_URL", "http://localhost:4000/v1/chat/completions")

@router.post("/ollama", response_model=LLMResponse)
def chat_ollama(req: LLMRequest):
    if not ollama:
        raise HTTPException(status_code=500, detail="Ollama não está instalado no backend.")
    model = req.model or "gemma:3b"
    try:
        response = ollama.chat(model=model, messages=[{"role": "user", "content": req.prompt}])
        return LLMResponse(response=response['message']['content'], model=model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar Ollama: {e}")

@router.post("/open-interpreter", response_model=LLMResponse)
def chat_open_interpreter(req: LLMRequest):
    model = req.model or "openinterpreter/o1"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": req.prompt}]
    }
    try:
        r = requests.post(OPEN_INTERPRETER_URL, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        # Compatível com OpenAI/Interpreter API
        resposta = data["choices"][0]["message"]["content"]
        return LLMResponse(response=resposta, model=model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar Open Interpreter: {e}") 