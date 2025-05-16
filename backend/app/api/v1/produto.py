from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...models.produto import Produto
from ...schemas.produto import ProdutoCreate, ProdutoRead
from typing import List
import easyocr
import re
import os

router = APIRouter(tags=["Produto"])

@router.post("/", response_model=ProdutoRead)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    db_produto = Produto(**produto.dict())
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    return db_produto

@router.get("/", response_model=List[ProdutoRead])
def listar_produtos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Produto).offset(skip).limit(limit).all()

@router.get("/{produto_id}", response_model=ProdutoRead)
def buscar_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@router.put("/{produto_id}", response_model=ProdutoRead)
def atualizar_produto(produto_id: int, produto: ProdutoCreate, db: Session = Depends(get_db)):
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    for key, value in produto.dict().items():
        setattr(db_produto, key, value)
    db.commit()
    db.refresh(db_produto)
    return db_produto

@router.delete("/{produto_id}")
def deletar_produto(produto_id: int, db: Session = Depends(get_db)):
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(db_produto)
    db.commit()
    return {"ok": True}

@router.post("/ocr", response_model=ProdutoRead, summary="Cria produto a partir de imagem de nota fiscal via OCR")
async def criar_produto_via_ocr(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo enviado não é uma imagem.")
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    try:
        reader = easyocr.Reader(['pt'])
        result = reader.readtext(temp_path, detail=0)
        texto = " ".join(result)
    finally:
        os.remove(temp_path)

    # Parsing simplificado (ajuste conforme o layout da sua nota fiscal)
    def extrair(pattern, texto, cast=str, default=None):
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            try:
                return cast(match.group(1).replace(',', '.'))
            except Exception:
                return default
        return default

    produto_data = {
        "nome": extrair(r"Produto[:\s]+([\w\s\-]+)", texto),
        "descricao": extrair(r"Descrição[:\s]+([\w\s\-]+)", texto),
        "fornecedor": extrair(r"Fornecedor[:\s]+([\w\s\-]+)", texto),
        "quantidade": extrair(r"Quantidade[:\s]+(\d+)", texto, int),
        "preco_unitario": extrair(r"Preço Unitário[:\s]+([\d\.,]+)", texto, float),
        "preco_liquido": extrair(r"Preço Líquido[:\s]+([\d\.,]+)", texto, float),
        "codigo_ncm": extrair(r"NCM[:\s]+([\w\d]+)", texto),
        "unidade": extrair(r"Unidade[:\s]+([\w]+)", texto),
        "data_emissao": extrair(r"Data de Emissão[:\s]+([\d/\-]+)", texto),
        "numero_nota": extrair(r"Nota Fiscal[:\s]+([\w\d]+)", texto),
        "cnpj_fornecedor": extrair(r"CNPJ[:\s]+([\d\./\-]+)", texto),
    }
    # Remover campos obrigatórios não encontrados
    obrigatorios = ["nome", "fornecedor", "quantidade", "preco_unitario", "preco_liquido"]
    for campo in obrigatorios:
        if not produto_data[campo]:
            raise HTTPException(status_code=422, detail=f"Campo obrigatório '{campo}' não encontrado na nota fiscal.")
    novo_produto = Produto(**produto_data)
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto 