from pydantic import BaseModel, ConfigDict

class NCMBase(BaseModel):
    codigo: str
    descricao: str

class NCMRead(NCMBase):
    model_config = ConfigDict(from_attributes=True)
