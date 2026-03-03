# Checklist final de entrega ao cliente (Desktop)

Use este checklist antes de marcar uma release desktop como pronta para entrega.

## 1) Build e artefatos
- [ ] Tag de release criada no padrão `v*-desktop.*`
- [ ] Workflow `windows-desktop-build` executado com sucesso
- [ ] Instalador `.exe` publicado como artifact
- [ ] `SHA256SUMS.txt` publicado como artifact

## 2) Validação funcional
- [x] Aplicativo abre sem erro após instalação
- [x] Login com usuário válido funciona
- [x] Navegação principal (Dashboard, Produtos, Estoque, PDV, Relatórios)
- [x] Fechar e reabrir app mantém comportamento esperado

## 3) Documentação de entrega
- [x] Release notes atualizada em `docs/releases/desktop-release-notes.md`
- [x] Requisitos mínimos informados
- [x] Instruções de instalação revisadas
- [x] Evidências do gate de VM limpa vinculadas

## 4) Aprovação final
- [ ] Responsável técnico aprovou a release
- [ ] Responsável de negócio aprovou a entrega ao cliente
- [ ] Data e responsável registrados no ticket/PR
