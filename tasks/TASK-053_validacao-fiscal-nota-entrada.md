---
task_id: TASK-053
title: "Validacao fiscal operacional de nota de entrada"
status: concluida
priority: alta
agent_chat_executable: "sim"
depends_on: ["TASK-029", "TASK-032", "TASK-044"]
---

## Objetivo

Mitigar erros tributarios em notas fiscais de entrada de fornecedores antes que
eles afetem custo, margem, precificacao e venda.

## Contexto

O projeto ja possuia parser XML de NFe, payload fiscal normalizado, auditoria
fiscal por regras e validacao cruzada. A lacuna era transformar isso em uma
validacao operacional mais direta para nota de entrada, com status claro e
achados focados em tributacao.

## Escopo implementado

1. Backend:
   - novo validador `backend/app/fiscal/entrada_validator.py`
   - status operacional: `aprovada`, `revisar` ou `reprovada`
   - score de risco operacional da nota de entrada
   - validacao de CNPJ do fornecedor com digito verificador
   - validacao de dados obrigatorios: numero, data e itens
   - validacao de CFOP na perspectiva do XML do fornecedor
   - validacao de coerencia CFOP x UF fornecedor/loja
   - validacao de NCM ausente
   - validacao de CST/CSOSN ausente
   - conferencia de valor de ICMS por item: base x aliquota = valor

2. Integracao:
   - `/api/v1/ocr/upload-arquivo` passa a retornar `validacao_entrada`
   - os achados da validacao de entrada tambem aparecem em `validacao_cruzada`
   - `/api/v1/fiscal-ai/validate-note` passa a retornar `validacao_entrada`
     quando `tipo_operacao` for `entrada`

3. Frontend:
   - tela de importacao de nota passa a exibir o status operacional da nota de
     entrada no painel de auditoria fiscal

## Criterios atendidos

- Nota com erro critico de tributacao retorna status `reprovada`.
- Nota com alerta tributario sem erro critico retorna status `revisar`.
- Nota sem inconsistencias operacionais detectadas retorna status `aprovada`.
- O usuario visualiza o status antes de concluir a importacao.
- Regras de negocio permanecem no backend.

## Fora de escopo

- Consulta online a SEFAZ.
- Validacao juridica completa da NF-e.
- Regras estaduais especificas por produto alem das tabelas internas atuais.
- Emissao fiscal.
- Escrituração SPED.

## Observacao

A validacao reduz risco operacional, mas nao substitui revisao contábil/fiscal
oficial quando houver duvida tributaria.
