# Politica de Versionamento da API

> **Versao:** 1.0.0 | **Data:** 2026-03-08 | **Status:** Vigente

---

## Visao Geral

A API adota versionamento explicito via prefixo de rota (`/api/v1/`, `/api/v2/`). Esta politica define o ciclo de vida de cada versao, criterios de depreciacao e regras para criacao de novos endpoints.

| Versao | Status | Uso |
|--------|--------|-----|
| `v1` | **Legado** - manutencao corretiva apenas | Endpoints existentes; sem novas features |
| `v2` | **Ativo** - versao oficial | Todas as novas funcionalidades |

> **Regra de Ouro:** toda nova feature deve ser criada em `/api/v2/`. Nunca adicionar endpoints novos em `/api/v1/`.

---

## Endpoints por Modulo

### Estoque

| Rota | Versao | Status | Substituto |
|------|--------|--------|------------|
| `GET /api/v1/estoque` | v1 |  Depreciado | `GET /api/v2/estoque` |
| `POST /api/v1/estoque` | v1 |  Depreciado | `POST /api/v2/estoque/transacao` |
| `GET /api/v1/estoque/{id}` | v1 |  Depreciado | `GET /api/v2/estoque/produto/{id}` |
| `PUT /api/v1/estoque/{id}` | v1 |  Depreciado | `POST /api/v2/estoque/transacao` (tipo: AJUSTE) |
| `DELETE /api/v1/estoque/{id}` | v1 |  Depreciado | `POST /api/v2/estoque/transacao` (tipo: AJUSTE) |
| `POST /api/v2/estoque/transacao` | v2 |  Ativo | - |
| `GET /api/v2/estoque` | v2 |  Ativo | - |
| `GET /api/v2/estoque/produto/{id}` | v2 |  Ativo | - |
| `GET /api/v2/estoque/historico/{id}` | v2 |  Ativo | - |
| `GET /api/v2/estoque/alertas` | v2 |  Ativo | - |
| `POST /api/v2/estoque/entrada-lote` | v2 |  Ativo | - |

### Movimentacao

| Rota | Versao | Status | Substituto |
|------|--------|--------|------------|
| `GET /api/v1/movimentacao` | v1 |  Em avaliacao | `GET /api/v2/estoque/historico/{id}` |
| `POST /api/v1/movimentacao` | v1 |  Em avaliacao | `POST /api/v2/estoque/transacao` |

> Pendente: avaliar se todos os consumidores ja usam `/api/v2/estoque` antes de definir data de sunset.

### Demais modulos (v1 ativo - sem prazo de depreciacao definido)

| Modulo | Prefixo | Status |
|--------|---------|--------|
| Users / Auth | `/api/v1/users` |  Ativo |
| Produtos | `/api/v1/produtos` |  Ativo |
| PDV | `/api/v1/pdv` |  Ativo |
| Vendas | `/api/v1/vendas` |  Ativo |
| Clientes | `/api/v1/clientes` |  Ativo |
| Fornecedores | `/api/v1/fornecedores` |  Ativo |
| Categorias | `/api/v1/categorias` |  Ativo |
| Orcamentos | `/api/v1/orcamentos` |  Ativo |
| Contas a Receber | `/api/v1/contas-receber` |  Ativo |
| Notas Fiscais | `/api/v1/notas-fiscais` |  Ativo |
| OCR / XML NFe | `/api/v1/ocr` |  Ativo |
| Relatorios | `/api/v1/relatorios` |  Ativo |
| Caixa Diario | `/api/v1/caixa` |  Ativo |
| Politica de Desconto | `/api/v1/politica-desconto` |  Ativo |
| NCM | `/api/v1/ncm` |  Ativo |
| Fiscal AI | `/api/v1/fiscal-ai` |  Ativo |
| AI | `/api/v1/ai` |  Ativo |

---

## Cronograma de Depreciacao

### Fase 1 - Concluida
- `/api/v2/estoque` implementado como substituto de `/api/v1/estoque`
- Header `Deprecation: true` adicionado nos endpoints legados de estoque

### Fase 2 - Em andamento
- Avaliar migracao de `/api/v1/movimentacao` para `/api/v2/estoque`
- Criterio: confirmar que todos os consumidores ja usam a rota v2
- Sunset: a definir apos avaliacao

### Fase 3 - Planejada
- Avaliar migracao dos demais modulos v1 para v2, priorizando por criticidade: Produtos, PDV, Vendas
- Criterio de promocao: cobertura de testes  80% no modulo v2 equivalente

---

## Regras para Novas Features

1. Criar sempre em `/api/v2/<modulo>`
2. Registrar o router em `backend/app/main.py` com `prefix="/api/v2/<modulo>"` e `tags=["<Modulo> V2"]`
3. Ao substituir um endpoint v1 existente:
   - Adicionar headers `Deprecation: true` e `Sunset: <data>` no endpoint v1
   - Atualizar a tabela neste documento
   - Registrar no `CHANGELOG.md` em secao `[Deprecated]`

---

## Processo de Breaking Changes

O aviso minimo antes de remover um endpoint e de **90 dias**.

```
1. Decisao de deprecar
2. Adicionar header Deprecation: true + Sunset: <data> no endpoint legado
3. Atualizar tabela neste documento
4. Registrar em CHANGELOG.md (secao Deprecated)
5. Na data do Sunset: remover endpoint + commit de remocao
```

Headers RFC 8594 usados nos endpoints depreciados:

```http
Deprecation: true
Sunset: <data RFC 1123>
Link: </api/v2/estoque>; rel="successor-version"
```

---

## Legenda

| Icone | Status | Significado |
|-------|--------|-------------|
|  | Ativo | Em producao, recebe novas features |
|  | Depreciado | Funcional, com data de remocao definida ou pendente |
|  | Em avaliacao | Legado sem data de sunset - aguardando analise |
|  | Removido | Endpoint nao existe mais |
