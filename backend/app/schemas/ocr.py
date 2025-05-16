from pydantic import BaseModel
from typing import List, Optional

class OCRResponse(BaseModel):
    texto: str
    produtos: Optional[List[str]] = None  # Para integração futura com extração inteligente
    quantidade: Optional[List[int]] = None
    valor: Optional[List[float]] = None 