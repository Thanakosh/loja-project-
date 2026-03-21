---
task_id: TASK-048
title: "Validar backend async em PostgreSQL"
status: pendente
priority: baixa
agent_chat_executable: "sim"
depends_on: ["TASK-042"]
---

## Objetivo

Executar uma validacao complementar do backend assincrono usando PostgreSQL,
confirmando que a migracao concluida em `TASK-042` tambem se comporta como
esperado fora do fluxo local baseado em SQLite.

### Contexto

A `TASK-042` concluiu a migracao da camada HTTP e da infraestrutura principal
para `AsyncSession`, com cobertura funcional ampla em testes locais. A
validacao em PostgreSQL nao e bloqueadora para o encerramento da migracao, mas
segue recomendada antes de merge mais rigoroso ou release.

### Acoes

1. Preparar ambiente de teste com PostgreSQL e driver async (`asyncpg`).
2. Configurar `DATABASE_URL` para um banco PostgreSQL descartavel de validacao.
3. Rodar uma bateria minima focada nos fluxos assincronos criticos:
   - `backend/tests/test_users.py`
   - `backend/tests/test_pdv.py`
   - `backend/tests/test_pdv_preco_minimo.py`
   - `backend/tests/test_caixa.py`
   - `backend/tests/test_configuracoes.py`
4. Registrar diferencas de comportamento entre SQLite e PostgreSQL, se houver.
5. Atualizar esta task com o resultado da validacao.

### Criterio de aceite

- Ambiente PostgreSQL de validacao sobe sem ajustes manuais nao documentados.
- Bateria minima async executa sem regressao critica.
- Eventuais divergencias de dialeto/transacao ficam documentadas.

### Branch sugerida

`docs/validar-backend-async-postgresql`
