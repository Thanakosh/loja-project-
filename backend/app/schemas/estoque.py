from pydantic import BaseModel, ConfigDict

class EstoqueBase(BaseModel):
    nome: str
    quantidade: int

class EstoqueCreate(EstoqueBase):
    pass

class EstoqueRead(EstoqueBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
