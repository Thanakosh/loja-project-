---
task_id: TASK-041
title: "Padronizar nomes e chain de migracoes Alembic"
status: pendente
priority: media
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Auditar as migracoes Alembic existentes, documentar a cadeia de dependencias
(revision chain) e padronizar a nomenclatura para facilitar manutencao futura.

### Contexto

O projeto tem 18 migracoes em `migrations/versions/`. A maioria segue o
padrao `YYYYMMDD_descricao.py`, mas uma usa hash Alembic puro:
`5065442b792a_cria_tabela_estoque.py`. A AGENTS.md define o padrao com data,
mas ele nao e uniformemente aplicado.

### Acoes

1. **Mapear a cadeia de revisoes:**
   ```bash
   cd backend
   alembic heads
   alembic history --verbose
   ```
   - Verificar se ha heads multiplos (conflito de migracoes).
   - Verificar se todas as migracoes formam uma cadeia linear.
   - Documentar a ordem exata de execucao.

2. **Verificar integridade:**
   ```bash
   alembic check
   ```
   - Confirmar que o banco esta sincronizado com os modelos.
   - Listar models que tem alteracoes nao refletidas em migracoes.

3. **Gerar documento de referencia** em `docs/alembic-chain.md`:
   - Tabela com: revision_id, data, descricao, depends_on
   - Indicar se ha migracoes que precisam ser renomeadas
   - Marcar a migracao com nome fora do padrao (`5065442b792a_...`)

4. **Se houver heads multiplos, resolver via merge:**
   ```bash
   alembic merge -m "merge_heads" <rev1> <rev2>
   ```

5. **Documentar no AGENTS.md** (se ainda nao estiver explicito):
   - Proibir `--autogenerate` sem revisao manual.
   - Sempre verificar `alembic history` antes de criar nova migracao.

###  Regras para o agente

- **NAO renomear arquivos de migracao** - isso pode quebrar a chain.
- **NAO deletar migracoes existentes** (conforme regra do AGENTS.md).
- Esta tarefa e de **auditoria e documentacao** - alteracoes apenas se
  houver heads multiplos que precisam de merge.

### Criterio de aceite

- `alembic heads` mostra uma unica head.
- `alembic history` executa sem erros.
- Documento `docs/alembic-chain.md` gerado com a cadeia completa.
- Eventuais conflitos de heads resolvidos.

### Branch sugerida

`docs/padronizar-migracoes-alembic`
