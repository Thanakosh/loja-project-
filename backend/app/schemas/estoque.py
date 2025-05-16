from pydantic import BaseModel

class EstoqueBase(BaseModel):
    nome: str
    quantidade: int

class EstoqueCreate(EstoqueBase):
    pass

class EstoqueRead(EstoqueBase):
    id: int

    class Config:
        orm_mode = True