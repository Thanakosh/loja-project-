# Checklist final de entrega ao cliente (Desktop)

Use este checklist antes de marcar uma release desktop como pronta para entrega.

## 1) Build e artefatos
- [ ] Tag de release criada no padrao `v*-desktop.*`
- [ ] Workflow `windows-desktop-build` executado com sucesso
- [ ] Instalador `.exe` publicado como artifact
- [ ] `SHA256SUMS.txt` publicado como artifact

## 2) Validacao funcional
- [x] Aplicativo abre sem erro apos instalacao
- [x] Login com usuario valido funciona
- [x] Navegacao principal (Dashboard, Produtos, Estoque, PDV, Relatorios)
- [x] Fechar e reabrir app mantem comportamento esperado

## 3) Documentacao de entrega
- [x] Release notes atualizada em `docs/releases/desktop-release-notes.md`
- [x] Requisitos minimos informados
- [x] Instrucoes de instalacao revisadas
- [x] Evidencias do gate de VM limpa vinculadas

## 4) Aprovacao final
- [ ] Responsavel tecnico aprovou a release
- [ ] Responsavel de negocio aprovou a entrega ao cliente
- [ ] Data e responsavel registrados no ticket/PR
