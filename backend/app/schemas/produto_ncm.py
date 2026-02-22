from pydantic import BaseModel
from typing import List, Optional

class ProdutoNCMUpdate(BaseModel):
    id: int
    codigo_ncm: Optional[str]

class LoteNCMUpdate(BaseModel):
    produtos: List[ProdutoNCMUpdate]
