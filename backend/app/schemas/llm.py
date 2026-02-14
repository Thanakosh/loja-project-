from pydantic import BaseModel, ConfigDict
from typing import Optional

class LLMRequest(BaseModel):
    prompt: str
    model: Optional[str] = None  # Ex: 'gemma:3b', 'llama3', 'mistral', 'openinterpreter/o1', etc.

class LLMResponse(BaseModel):
    response: str
    model: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
