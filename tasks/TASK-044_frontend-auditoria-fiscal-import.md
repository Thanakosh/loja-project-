---
task_id: TASK-044
title: "Frontend: exibir auditoria fiscal na importação de XML"
status: pendente
priority: alta
agent_chat_executable: "sim"
depends_on: []
---

## Objetivo

Exibir no frontend (`ImportarNota.tsx`) os resultados de auditoria fiscal e
validação cruzada que o backend **já retorna** no endpoint `/ocr/upload-arquivo`.

### Contexto

O backend já integra auditoria fiscal na importação de XML (Fase 1 do plano
fiscal). O resultado do upload já inclui `auditoria_fiscal` (com classificação,
score, confiança, explicação e fatores) e `validacao_cruzada` (lista de
findings com severidade). **O frontend ignora esses dados.**

Evidência: `test_ocr_fiscal_validation.py` confirma que a API retorna os
campos corretamente.

### Ações

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
   - Badge com classificação de risco:
     - 🟢 `baixo` → badge verde
     - 🟡 `medio` → badge amarelo
     - 🔴 `alto` → badge vermelho
   - Score numérico (0-100) com barra visual
   - Lista colapsável de fatores com ícone ✅/❌/⚪ por resultado
   - Lista de findings da validação cruzada com severidade
   - Explicação textual da classificação

3. **Integrar na etapa de revisão do `ImportarNota.tsx`:**
   - Extrair `auditoria_fiscal` e `validacao_cruzada` do resultado do OCR
   - Renderizar `PainelAuditoriaFiscal` na área de revisão da nota
   - Se `classificacao === 'alto'`, exibir alerta chamativo antes de permitir
     a confirmação da importação (não bloquear, apenas alertar)

4. **Tratamento de ausência:**
   - Se `auditoria_fiscal` for `null` (ex: erro no backend), não quebrar o fluxo
   - Exibir mensagem "Auditoria fiscal indisponível" com estilo discreto

### Critério de aceite

- Ao importar um XML, o painel de auditoria fiscal é exibido na revisão.
- Badge de risco visível e correto (baixo/médio/alto).
- Fatores e findings listados de forma legível.
- Alerta visual para notas classificadas como "alto" risco.
- Build sem erros.

### Branch sugerida

`frontend/exibir-auditoria-fiscal-import`
