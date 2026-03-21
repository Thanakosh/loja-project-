---
task_id: TASK-044
title: "Frontend: exibir auditoria fiscal na importacao de XML"
status: concluida
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Exibir no frontend (`ImportarNota.tsx`) os resultados de auditoria fiscal e
validacao cruzada que o backend **ja retorna** no endpoint `/ocr/upload-arquivo`.

### Contexto

O backend ja integra auditoria fiscal na importacao de XML (Fase 1 do plano
fiscal). O resultado do upload ja inclui `auditoria_fiscal` (com classificacao,
score, confianca, explicacao e fatores) e `validacao_cruzada` (lista de
findings com severidade). **O frontend ignora esses dados.**

Evidencia: `test_ocr_fiscal_validation.py` confirma que a API retorna os
campos corretamente.

### Acoes

1. **Criar interfaces TypeScript** em `frontend/src/types/`:
   ```typescript
   interface AuditoriaFiscal {
     classificacao: 'baixo' | 'medio' | 'alto'
     score: number
     confianca: number
     explicacao: string
     fatores: FatorAuditoria[]
   }

   interface FatorAuditoria {
     regra: string
     resultado: 'passou' | 'falha' | 'ignorado'
     peso: number
     detalhe: string
   }

   interface ValidacaoCruzadaItem {
     regra: string
     severidade: string
     item_sequencia: number | null
     descricao: string
   }
   ```

2. **Criar componente `PainelAuditoriaFiscal.tsx`** em `frontend/src/components/`:
   - Badge com classificacao de risco:
     -  `baixo`  badge verde
     -  `medio`  badge amarelo
     -  `alto`  badge vermelho
   - Score numerico (0-100) com barra visual
   - Lista colapsavel de fatores com icone // por resultado
   - Lista de findings da validacao cruzada com severidade
   - Explicacao textual da classificacao

3. **Integrar na etapa de revisao do `ImportarNota.tsx`:**
   - Extrair `auditoria_fiscal` e `validacao_cruzada` do resultado do OCR
   - Renderizar `PainelAuditoriaFiscal` na area de revisao da nota
   - Se `classificacao === 'alto'`, exibir alerta chamativo antes de permitir
     a confirmacao da importacao (nao bloquear, apenas alertar)

4. **Tratamento de ausencia:**
   - Se `auditoria_fiscal` for `null` (ex: erro no backend), nao quebrar o fluxo
   - Exibir mensagem "Auditoria fiscal indisponivel" com estilo discreto

### Criterio de aceite

- Ao importar um XML, o painel de auditoria fiscal e exibido na revisao.
- Badge de risco visivel e correto (baixo/medio/alto).
- Fatores e findings listados de forma legivel.
- Alerta visual para notas classificadas como "alto" risco.
- Build sem erros.

### Branch sugerida

`frontend/exibir-auditoria-fiscal-import`
