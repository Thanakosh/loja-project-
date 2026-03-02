# Evidências — TASK-019 (Gate de instalação limpa)

## Contexto
Evidências da validação manual da instalação desktop em VM Windows limpa,
conforme gate obrigatório de qualidade antes da entrega ao cliente.

## Resultado
- **Status:** Aprovado
- **Data da validação:** 2026-03-02
- **Ambiente:** VM Windows limpa (sem Node/Python previamente instalados)

## Checklist executado
- [x] Instalação concluída sem erro
- [x] Aplicação abriu e tela de login carregou
- [x] Login com usuário válido funcionou
- [x] Navegação principal executada sem travamentos
- [x] Comunicação com API sem erro de CORS/SSL
- [x] Fechar e reabrir app manteve comportamento esperado
- [x] Desinstalação sem resíduos críticos

## Referências
- Task do gate: `tasks/TASK-019_gate-validacao-instalacao-limpa.md`
- Nota de release desktop: `docs/releases/desktop-release-notes.md`
