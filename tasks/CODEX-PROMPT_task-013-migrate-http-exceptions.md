# CODEX PROMPT - TASK-013: Migrar HTTPException para BusinessException

## Contexto

O projeto ja possui toda a infraestrutura de tratamento centralizado de erros implementada:

- `backend/app/core/exceptions.py` - classes de negocio tipadas (`BusinessException`, `EstoqueInsuficienteError`, etc.)
- `backend/app/core/error_handlers.py` - handler global registrado no FastAPI em `main.py`
- O formato de resposta de erro padronizado ja e:
  ```json
  { "code": "string", "message": "string", "details": {}, "trace_id": "uuid" }
  ```

**O problema:** varios routers antigos ainda usam `raise HTTPException(status_code=..., detail="...")` diretamente,
em vez de lancar `BusinessException` ou subclasses tipadas. Isso gera respostas inconsistentes.

## Tarefa

Crie a branch `codex/migrar-http-exceptions-para-business-exception` a partir do `main` e refatore os routers listados abaixo.

### Branch e Commit

```
branch: codex/migrar-http-exceptions-para-business-exception
commit: refactor(api): migra HTTPException legado para BusinessException padronizada
```

---

## Arquivos a refatorar

### 1. `backend/app/api/v1/contas_receber.py`

Ocorrencias a migrar:
- linha ~92: `raise HTTPException(status_code=404, detail="Conta nao encontrada")`
   Criar `ContaNaoEncontradaError(BusinessException)` em `exceptions.py` com `code="conta_nao_encontrada"`, `status_code=404`
- linha ~95: `raise HTTPException(status_code=400, detail="Esta conta ja foi baixada anteriormente.")`
   Criar `ContaJaBaixadaError(BusinessException)` em `exceptions.py` com `code="conta_ja_baixada"`, `status_code=400`

### 2. `backend/app/api/v1/estoque.py`

Ocorrencias a migrar (linhas ~42, ~55, ~74):
- Todas sao `raise HTTPException(status_code=404, detail="Item nao encontrado")`
   Criar `ItemEstoqueNaoEncontradoError(BusinessException)` em `exceptions.py` com `code="item_estoque_nao_encontrado"`, `status_code=404`

### 3. `backend/app/api/v1/fornecedores.py`

Ocorrencias a migrar:
- `status_code=404, detail="Fornecedor nao encontrado"` (linhas ~57, ~96, ~126, ~149)
   Criar `FornecedorNaoEncontradoError` com `code="fornecedor_nao_encontrado"`, `status_code=404`
- `status_code=400, detail="CNPJ ja cadastrado"` (linhas ~73, ~105)
   Criar `CnpjJaCadastradoError` com `code="cnpj_ja_cadastrado"`, `status_code=400`
- `status_code=400, detail="Fornecedor ja esta inativo"` (linha ~129)
   Criar `FornecedorJaInativoError` com `code="fornecedor_ja_inativo"`, `status_code=400`
- `status_code=400, detail="Fornecedor ja esta ativo"` (linha ~152)
   Criar `FornecedorJaAtivoError` com `code="fornecedor_ja_ativo"`, `status_code=400`

### 4. `backend/app/api/v1/orcamento.py`

Ocorrencias a migrar:
- `status_code=422, detail="deve informar cliente_id ou cliente_nome"` (linha ~43)
   Criar `ClienteNaoIdentificadoError` com `code="cliente_nao_identificado"`, `status_code=422`
- `status_code=404, detail="Orcamento nao encontrado"` (linhas ~115, ~136, ~180, ~204)
   Criar `OrcamentoNaoEncontradoError` com `code="orcamento_nao_encontrado"`, `status_code=404`
- `status_code=400, detail="Apenas orcamentos abertos podem ser..."` (linha ~139)
   Criar `OrcamentoNaoAbertoError` com `code="orcamento_nao_aberto"`, `status_code=400`
- `status_code=400, detail="Apenas orcamentos abertos ou aprovados..."` (linha ~207)
   Criar `OrcamentoNaoCancelavelError` com `code="orcamento_nao_cancelavel"`, `status_code=400`
- `status_code=400, detail="Nenhum item elegivel para venda"` (linha ~221)
   Criar `SemItensElegiveisError` com `code="sem_itens_elegiveis"`, `status_code=400`

### 5. `backend/app/api/v1/llm.py`

Ocorrencia:
- `raise HTTPException(...)` na linha ~27 (erro de dependencia/configuracao)
   Se for erro de configuracao do servidor, use `BusinessException` com `code="servico_indisponivel"`, `status_code=503`

### 6. `backend/app/api/v1/users.py`

Ocorrencias (linhas ~45, ~80, ~123):
- Manter o `raise HTTPException` para erros de autenticacao (401, 403) que ja sao tratados pelo handler do Starlette.
- Converter apenas os 404 de "usuario nao encontrado" para `UsuarioNaoEncontradoError` se aplicavel.

>  **NAO remover** o import de `HTTPException` dos arquivos que ainda o usam para 401/403 de auth - esses sao tratados corretamente pelo `starlette_http_exception_handler`.

---

## Onde adicionar as novas excecoes

Arquivo: `backend/app/core/exceptions.py`

Padrao obrigatorio (seguir o mesmo padrao das ja existentes):
```python
class FornecedorNaoEncontradoError(BusinessException):
    def __init__(self, *, details: Any | None = None) -> None:
        super().__init__(
            code="fornecedor_nao_encontrado",
            message="Fornecedor nao encontrado",
            status_code=404,
            details=details,
        )
```

---

## Testes obrigatorios

Adicionar em `backend/tests/test_error_handlers.py` (criar se nao existir):
- Teste que endpoint de fornecedor inexistente retorna `{"code": "fornecedor_nao_encontrado", "trace_id": ...}`
- Teste que orcamento inexistente retorna `{"code": "orcamento_nao_encontrado", "trace_id": ...}`
- Teste que conta ja baixada retorna `{"code": "conta_ja_baixada", "trace_id": ...}`
- Verificar que `trace_id` esta presente em **todas** as respostas de erro acima

---

## Criterios de aceite

- [ ] Nenhum dos arquivos listados usa `raise HTTPException(status_code=404, detail="...")` para erros de negocio
- [ ] Todas as novas excecoes estao em `backend/app/core/exceptions.py`
- [ ] `pytest tests/ -v` passa sem erros
- [ ] Nenhum arquivo `.env` ou dado sensivel foi commitado
- [ ] Commit segue Conventional Commits: `refactor(api): migra HTTPException legado para BusinessException padronizada`
- [ ] `CHANGELOG.md` atualizado na secao `[Unreleased]`
