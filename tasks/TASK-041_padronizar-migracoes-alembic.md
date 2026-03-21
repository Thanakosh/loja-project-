---
task_id: TASK-041
title: "Padronizar nomes e chain de migrações Alembic"
status: concluida
priority: media
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Auditar as migrações Alembic existentes, documentar a cadeia de dependências
(revision chain) e padronizar a nomenclatura para facilitar manutenção futura.

### Contexto

O projeto tem 18 migrações em `migrations/versions/`. A maioria segue o
padrão `YYYYMMDD_descricao.py`, mas uma usa hash Alembic puro:
`5065442b792a_cria_tabela_estoque.py`. A AGENTS.md define o padrão com data,
mas ele não é uniformemente aplicado.

### Ações

1. **Mapear a cadeia de revisões:**
   ```bash
   cd backend
   alembic heads
   alembic history --verbose
   ```
   - Verificar se há heads múltiplos (conflito de migrações).
   - Verificar se todas as migrações formam uma cadeia linear.
   - Documentar a ordem exata de execução.

2. **Verificar integridade:**
   ```bash
   alembic check
   ```
   - Confirmar que o banco está sincronizado com os modelos.
   - Listar models que têm alterações não refletidas em migrações.

3. **Gerar documento de referência** em `docs/alembic-chain.md`:
   - Tabela com: revision_id, data, descrição, depends_on
   - Indicar se há migrações que precisam ser renomeadas
   - Marcar a migração com nome fora do padrão (`5065442b792a_...`)

4. **Se houver heads múltiplos, resolver via merge:**
   ```bash
   alembic merge -m "merge_heads" <rev1> <rev2>
   ```

5. **Documentar no AGENTS.md** (se ainda não estiver explicito):
   - Proibir `--autogenerate` sem revisão manual.
   - Sempre verificar `alembic history` antes de criar nova migração.

### ⚠️ Regras para o agente

- **NÃO renomear arquivos de migração** — isso pode quebrar a chain.
- **NÃO deletar migrações existentes** (conforme regra do AGENTS.md).
- Esta tarefa é de **auditoria e documentação** — alterações apenas se
  houver heads múltiplos que precisam de merge.

### Critério de aceite

- `alembic heads` mostra uma única head.
- `alembic history` executa sem erros.
- Documento `docs/alembic-chain.md` gerado com a cadeia completa.
- Eventuais conflitos de heads resolvidos.

### Branch sugerida

`docs/padronizar-migracoes-alembic`

## Atualizacao de status

- `alembic heads` retornou uma unica head: `20260321_configuracao_loja`.
- `alembic history --verbose` confirmou cadeia linear.
- Documento gerado em `docs/alembic-chain.md` com a chain completa e destaque para `5065442b792a_cria_tabela_estoque.py`.
- `alembic check` falhou por configuracao local invalida (`DEBUG=release`), fato documentado no relatorio.
- `AGENTS.md` atualizado para exigir revisao manual de `--autogenerate` e verificacao previa com `alembic history --verbose`.
