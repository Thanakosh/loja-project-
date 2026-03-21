---
task_id: TASK-046
title: "Frontend: unificacao de nomes de produtos similares na importacao"
status: pendente
priority: media
agent_chat_executable: "sim"
depends_on: ["TASK-044"]
---

## Objetivo

Evoluir o modal de duplicatas na importacao de XML para permitir que o
usuario escolha um nome unificado quando a IA detectar produtos com nomes
similares.

### Contexto

O backend ja possui deteccao de duplicatas via `/ai/check-duplicate`
(`ai/duplicate_detector.py`). O frontend `ImportarNota.tsx` ja exibe um
modal quando duplicatas sao detectadas, mas **nao oferece a opcao de unificar
nomes** - o operador ve o alerta mas nao pode agir sobre ele.

### Acoes

1. **Evoluir o `ModalDuplicatas`** em `ImportarNota.tsx` (ou extrair para
   componente separado `ModalDuplicatas.tsx`):
   - Para cada item similar detectado, exibir:
     - Nome importado (do XML)
     - Nome(s) existente(s) no sistema (da deteccao de duplicatas)
     - Opcoes via radio button:
       -  "Usar nome importado" (default)
       -  "Usar nome existente" (seleciona do cadastro)
       -  "Digitar nome personalizado" (campo de texto livre)
   - Campo de texto para nome personalizado (habilitado apenas quando selecionado)

2. **Atualizar logica de importacao:**
   - Se o usuario escolher "Usar nome existente" e `aiProdutoId` for valido:
     o backend ja faz merge automatico (soma estoque ao produto existente)
   - Se o usuario digitar nome personalizado: atualizar o nome do item na
     lista antes de enviar ao backend

3. **Melhorar UX do modal:**
   - Mostrar score de similaridade para cada match
   - Destacar visualmente as diferencas entre nomes (ex: "Cabo 2.5mm" vs "CABO 2,5MM")
   - Botao de "Aplicar a Todos com Mesmo Match" para acoes repetitivas

### Criterio de aceite

- Modal de duplicatas oferece 3 opcoes de nome para cada item similar.
- Escolher "nome existente" resulta em merge de estoque.
- Escolher "nome personalizado" envia o nome digitado ao backend.
- Build sem erros.

### Branch sugerida

`frontend/unificacao-nomes-duplicatas`
