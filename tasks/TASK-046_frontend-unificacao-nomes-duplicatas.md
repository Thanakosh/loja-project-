---
task_id: TASK-046
title: "Frontend: unificação de nomes de produtos similares na importação"
status: pendente
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-044"]
---

## Objetivo

Evoluir o modal de duplicatas na importação de XML para permitir que o
usuário escolha um nome unificado quando a IA detectar produtos com nomes
similares.

### Contexto

O backend já possui detecção de duplicatas via `/ai/check-duplicate`
(`ai/duplicate_detector.py`). O frontend `ImportarNota.tsx` já exibe um
modal quando duplicatas são detectadas, mas **não oferece a opção de unificar
nomes** — o operador vê o alerta mas não pode agir sobre ele.

### Ações

1. **Evoluir o `ModalDuplicatas`** em `ImportarNota.tsx` (ou extrair para
   componente separado `ModalDuplicatas.tsx`):
   - Para cada item similar detectado, exibir:
     - Nome importado (do XML)
     - Nome(s) existente(s) no sistema (da detecção de duplicatas)
     - Opções via radio button:
       - ○ "Usar nome importado" (default)
       - ○ "Usar nome existente" (seleciona do cadastro)
       - ○ "Digitar nome personalizado" (campo de texto livre)
   - Campo de texto para nome personalizado (habilitado apenas quando selecionado)

2. **Atualizar lógica de importação:**
   - Se o usuário escolher "Usar nome existente" e `aiProdutoId` for válido:
     o backend já faz merge automático (soma estoque ao produto existente)
   - Se o usuário digitar nome personalizado: atualizar o nome do item na
     lista antes de enviar ao backend

3. **Melhorar UX do modal:**
   - Mostrar score de similaridade para cada match
   - Destacar visualmente as diferenças entre nomes (ex: "Cabo 2.5mm" vs "CABO 2,5MM")
   - Botão de "Aplicar a Todos com Mesmo Match" para ações repetitivas

### Critério de aceite

- Modal de duplicatas oferece 3 opções de nome para cada item similar.
- Escolher "nome existente" resulta em merge de estoque.
- Escolher "nome personalizado" envia o nome digitado ao backend.
- Build sem erros.

### Branch sugerida

`frontend/unificacao-nomes-duplicatas`
