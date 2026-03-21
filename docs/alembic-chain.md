# Cadeia de Migracoes Alembic

Data da auditoria: 2026-03-21

## Resumo

- Quantidade de migracoes em `migrations/versions/`: 19 arquivos Python
- Resultado de `alembic heads`: uma unica head
- Head atual: `20260321_configuracao_loja`
- Estado da chain: linear
- Ponto fora do padrao de nomenclatura: `5065442b792a_cria_tabela_estoque.py`

## Comandos executados

```powershell
alembic heads
alembic history --verbose
alembic check
```

## Resultado operacional

### `alembic heads`

Retornou apenas:

```text
20260321_configuracao_loja (head)
```

Conclusao: nao ha conflito de heads no estado atual.

### `alembic history --verbose`

Executou com sucesso e confirmou uma cadeia linear da base ate a head atual.

### `alembic check`

Falhou antes da comparacao de schema por erro de configuracao do ambiente:

```text
ValidationError: Settings
DEBUG
Input should be a valid boolean, unable to interpret input
input_value='release'
```

Conclusao: o bloqueio atual nao indica necessariamente divergencia entre models e migracoes; indica que a carga de configuracao do app nao esta valida para o comando Alembic no ambiente local atual.

## Chain de revisoes

| Ordem | revision_id | revises | Arquivo | Observacao |
|------|-------------|---------|---------|------------|
| 1 | `5065442b792a` | `<base>` | `5065442b792a_cria_tabela_estoque.py` | unico arquivo fora do padrao `YYYYMMDD_descricao.py` |
| 2 | `refactor_estoque_v2` | `5065442b792a` | `20260214_refactor_estoque_transacoes.py` | revision id nao segue data, arquivo segue |
| 3 | `20260220_add_fornecedor_table` | `refactor_estoque_v2` | `20260220_add_fornecedor_table.py` | cadeia linear |
| 4 | `20260220_add_pdv_columns` | `20260220_add_fornecedor_table` | `20260220_add_pdv_columns.py` | cadeia linear |
| 5 | `20260221_refactor_orcamento` | `20260220_add_pdv_columns` | `20260221_refactor_orcamento.py` | cadeia linear |
| 6 | `20260222_add_ncm_table` | `20260221_refactor_orcamento` | `20260222_add_ncm_table.py` | cadeia linear |
| 7 | `20260302_add_categoria_produto` | `20260222_add_ncm_table` | `20260302_add_categoria_produto.py` | cadeia linear |
| 8 | `20260302_unidade_medida_produto` | `20260302_add_categoria_produto` | `20260302_unidade_medida_produto.py` | cadeia linear |
| 9 | `20260302_precificacao_avancada` | `20260302_unidade_medida_produto` | `20260302_precificacao_avancada.py` | cadeia linear |
| 10 | `20260303_add_username_to_user` | `20260302_precificacao_avancada` | `20260303_add_username_to_user.py` | cadeia linear |
| 11 | `20260303_caixa_diario` | `20260303_add_username_to_user` | `20260303_caixa_diario.py` | cadeia linear |
| 12 | `20260303_pdv_barcode_autorizacao_pdf` | `20260303_caixa_diario` | `20260303_pdv_barcode_autorizacao_pdf.py` | cadeia linear |
| 13 | `20260303_politica_desconto` | `20260303_pdv_barcode_autorizacao_pdf` | `20260303_politica_desconto_progressivo.py` | revision id resumido, arquivo segue padrao |
| 14 | `20260303_autorizacao_snapshot` | `20260303_politica_desconto` | `20260303_autorizacao_snapshot.py` | cadeia linear |
| 15 | `20260303_desconto_auditoria` | `20260303_autorizacao_snapshot` | `20260303_desconto_auditoria.py` | cadeia linear |
| 16 | `20260303_produto_embedding` | `20260303_desconto_auditoria` | `20260303_produto_embedding.py` | cadeia linear |
| 17 | `20260303_fiscal_feedback` | `20260303_produto_embedding` | `20260303_fiscal_feedback.py` | cadeia linear |
| 18 | `20260308_adiciona_campos_feedback_fiscal` | `20260303_fiscal_feedback` | `20260308_adiciona_campos_feedback_fiscal.py` | cadeia linear |
| 19 | `20260321_configuracao_loja` | `20260308_adiciona_campos_feedback_fiscal` | `20260321_configuracao_loja.py` | head atual |

## Avaliacao de padronizacao

Itens observados:

- O nome de arquivo esta padronizado com data em quase toda a chain.
- O arquivo `5065442b792a_cria_tabela_estoque.py` foge ao padrao esperado e deve permanecer como esta para nao quebrar a chain.
- Alguns `revision_id` internos nao seguem o mesmo padrao de data:
  - `5065442b792a`
  - `refactor_estoque_v2`
  - `20260303_politica_desconto`

Conclusao pratica:

- Nao renomear arquivos antigos.
- Manter o padrao `YYYYMMDD_descricao.py` para todos os novos arquivos.
- Revisar manualmente `revision_id`, `down_revision` e operacoes geradas antes de qualquer nova migracao entrar na branch.

## Recomendacoes

1. Corrigir a configuracao local usada pelo Alembic para que `alembic check` rode com `DEBUG` booleano valido.
2. Antes de criar nova migracao, sempre executar `alembic history --verbose` para confirmar a chain esperada.
3. Evitar `alembic revision --autogenerate` sem revisao manual do diff gerado.
4. Nao renomear migracoes existentes, mesmo quando o padrao antigo estiver fora da convencao atual.
