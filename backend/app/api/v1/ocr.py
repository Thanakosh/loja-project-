from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from ...core.database import get_db
import easyocr
import os
from ...schemas.ocr import OCRResponse
import re

router = APIRouter(tags=["OCR"])

@router.post("/upload", summary="Faz upload de imagem e extrai texto via OCR", response_model=OCRResponse)
async def upload_ocr(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo enviado não é uma imagem.")
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    try:
        reader = easyocr.Reader(['pt'])
        result = reader.readtext(temp_path, detail=0)
        texto_extraido = " ".join(result)
    finally:
        os.remove(temp_path)
    return OCRResponse(texto=texto_extraido)

@router.post("/extrair-dados", response_model=OCRResponse, summary="Extrai produtos, quantidades e valores do texto OCR")
def extrair_dados_ocr(
    texto: str = Body(..., embed=True)
):
    # Regex simples para Produto, Quantidade, Valor
    produtos = re.findall(r"Produto: ([\w\s]+)", texto, re.IGNORECASE)
    quantidades = [int(q) for q in re.findall(r"Quantidade: (\d+)", texto, re.IGNORECASE)]
    valores = [float(v.replace(',', '.')) for v in re.findall(r"Valor: ([\d\.,]+)", texto, re.IGNORECASE)]
    return OCRResponse(
        texto=texto,
        produtos=produtos if produtos else None,
        quantidade=quantidades if quantidades else None,
        valor=valores if valores else None
    ) 