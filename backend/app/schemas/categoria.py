from pydantic import BaseModel, ConfigDict, Field


class CategoriaBase(BaseModel):
    nome: str
    parent_id: int | None = None
    ativo: bool = True


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nome: str | None = None
    parent_id: int | None = None
    ativo: bool | None = None


class CategoriaRead(CategoriaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CategoriaTreeNode(BaseModel):
    id: int
    nome: str
    parent_id: int | None = None
    ativo: bool
    children: list["CategoriaTreeNode"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


CategoriaTreeNode.model_rebuild()
