from fastapi import APIRouter, HTTPException, Request
from ...core.limiter import limiter
from ...schemas.llm import LLMRequest, LLMResponse
from ...schemas.ocr import NotaFiscalExtraida, ProdutoExtraido
import os
import requests
import json
import re
from typing import Optional

try:
    import ollama
except ImportError:
    ollama = None

from ...core.config import settings

router = APIRouter(tags=["LLM"])

@router.post("/ollama", response_model=LLMResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
def chat_ollama(request: Request, req: LLMRequest):
    """Chat com modelo local Ollama"""
    if not ollama:
        raise HTTPException(status_code=500, detail="Ollama não está instalado no backend.")
    model = req.model or "gemma:3b"
    try:
        response = ollama.chat(model=model, messages=[{"role": "user", "content": req.prompt}])
        return LLMResponse(response=response['message']['content'], model=model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar Ollama: {e}")

@router.post("/open-interpreter", response_model=LLMResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
def chat_open_interpreter(request: Request, req: LLMRequest):
    """Chat com Open Interpreter"""
    model = req.model or "openinterpreter/o1"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": req.prompt}]
    }
    try:
        r = requests.post(settings.OPEN_INTERPRETER_URL, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        resposta = data["choices"][0]["message"]["content"]
        return LLMResponse(response=resposta, model=model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar Open Interpreter: {e}")


async def processar_nota_fiscal_com_llm(texto_ocr: str) -> NotaFiscalExtraida:
    """
    Processa texto extraído de nota fiscal usando LLM para análise inteligente.
    Retorna dados estruturados da nota fiscal.
    """
    
    prompt = f"""Você é um especialista em análise de notas fiscais brasileiras. 
Analise o texto OCR abaixo e extraia as seguintes informações em formato JSON:

1. Fornecedor (razão social)
2. CNPJ do fornecedor
3. Número da nota fiscal
4. Data de emissão (formato YYYY-MM-DD)
5. Lista de produtos, cada um contendo:
   - nome: nome do produto
   - quantidade: quantidade numérica
   - preco_unitario: preço unitário em float
   - unidade: unidade de medida (ex: UN, KG, CX)
   - codigo_ncm: código NCM se disponível
6. Valor total da nota

Texto OCR:
{texto_ocr}

Retorne APENAS um objeto JSON válido, sem explicações adicionais. Formato:
{{
  "fornecedor": "string",
  "cnpj_fornecedor": "string",
  "numero_nota": "string",
  "data_emissao": "YYYY-MM-DD",
  "produtos": [
    {{
      "nome": "string",
      "quantidade": number,
      "preco_unitario": number,
      "unidade": "string",
      "codigo_ncm": "string"
    }}
  ],
  "valor_total": number
}}
"""
    
    try:
        # Tentar usar Ollama primeiro
        if ollama:
            try:
                response = ollama.chat(
                    model="gemma:3b",
                    messages=[{"role": "user", "content": prompt}]
                )
                resposta_texto = response['message']['content']
            except Exception:
                # Se Ollama falhar, tentar Open Interpreter
                resposta_texto = await _usar_open_interpreter(prompt)
        else:
            resposta_texto = await _usar_open_interpreter(prompt)
        
        # Extrair JSON da resposta
        json_match = re.search(r'\{.*\}', resposta_texto, re.DOTALL)
        if not json_match:
            raise ValueError("LLM não retornou JSON válido")
        
        dados = json.loads(json_match.group())
        
        # Validar e criar objeto NotaFiscalExtraida
        produtos = [
            ProdutoExtraido(**p) for p in dados.get("produtos", [])
        ]
        
        return NotaFiscalExtraida(
            fornecedor=dados.get("fornecedor", ""),
            cnpj_fornecedor=dados.get("cnpj_fornecedor"),
            numero_nota=dados.get("numero_nota"),
            data_emissao=dados.get("data_emissao"),
            produtos=produtos,
            valor_total=dados.get("valor_total", 0.0)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao processar nota fiscal com LLM: {str(e)}"
        )


async def _usar_open_interpreter(prompt: str) -> str:
    """Helper para usar Open Interpreter"""
    payload = {
        "model": "openinterpreter/o1",
        "messages": [{"role": "user", "content": prompt}]
    }
    r = requests.post(settings.OPEN_INTERPRETER_URL, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


@router.post("/analisar-nota-fiscal", response_model=NotaFiscalExtraida)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def analisar_nota_fiscal_endpoint(request: Request, req: LLMRequest):
    """
    Endpoint para analisar texto de nota fiscal usando LLM.
    O texto deve ser o resultado do OCR.
    """
    return await processar_nota_fiscal_com_llm(req.prompt)
