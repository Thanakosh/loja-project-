# Release Notes - Desktop Windows

## Versao
- **Tag de release:** `v2.2.0-desktop.1`
- **Data prevista de publicacao:** 2026-03-02

## Mudancas da versao (changelog)
- Pipeline de build desktop Windows consolidado com geracao de instalador `.exe`.
- Publicacao de checksum SHA256 para validacao de integridade do instalador.
- Formalizacao do gate de validacao em instalacao limpa (VM Windows).

## Requisitos minimos de sistema
- **Sistema operacional:** Windows 10 ou Windows 11 (64 bits)
- **Arquitetura:** x64
- **Memoria RAM:** 4 GB (recomendado: 8 GB)
- **Espaco livre em disco:** 500 MB
- **Conectividade:** acesso de rede para comunicacao com API remota

## Instrucoes de instalacao
1. Baixar o instalador `.exe` publicado nos artifacts da workflow `windows-desktop-build`.
2. Baixar o arquivo `SHA256SUMS.txt` do artifact de checksum.
3. Validar a integridade do instalador com PowerShell:
   ```powershell
   Get-FileHash .\Loja-Setup.exe -Algorithm SHA256
   ```
4. Comparar o hash obtido com o valor correspondente em `SHA256SUMS.txt`.
5. Executar o instalador com duplo clique e concluir o assistente.
6. Abrir o aplicativo e realizar login com credenciais validas.

## Evidencias do gate de instalacao limpa (TASK-019)
- Evidencias e checklist executado: [`docs/evidencias/TASK-019_validacao-vm-limpa.md`](../evidencias/TASK-019_validacao-vm-limpa.md).
- Registro da conclusao da task: [`tasks/TASK-019_gate-validacao-instalacao-limpa.md`](../../tasks/TASK-019_gate-validacao-instalacao-limpa.md).
