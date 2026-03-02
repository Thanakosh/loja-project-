# Release Notes — Desktop Windows

## Versão
- **Tag de release:** `v2.2.0-desktop.1`
- **Data prevista de publicação:** 2026-03-02

## Mudanças da versão (changelog)
- Pipeline de build desktop Windows consolidado com geração de instalador `.exe`.
- Publicação de checksum SHA256 para validação de integridade do instalador.
- Formalização do gate de validação em instalação limpa (VM Windows).

## Requisitos mínimos de sistema
- **Sistema operacional:** Windows 10 ou Windows 11 (64 bits)
- **Arquitetura:** x64
- **Memória RAM:** 4 GB (recomendado: 8 GB)
- **Espaço livre em disco:** 500 MB
- **Conectividade:** acesso de rede para comunicação com API remota

## Instruções de instalação
1. Baixar o instalador `.exe` publicado nos artifacts da workflow `windows-desktop-build`.
2. Baixar o arquivo `SHA256SUMS.txt` do artifact de checksum.
3. Validar a integridade do instalador com PowerShell:
   ```powershell
   Get-FileHash .\Loja-Setup.exe -Algorithm SHA256
   ```
4. Comparar o hash obtido com o valor correspondente em `SHA256SUMS.txt`.
5. Executar o instalador com duplo clique e concluir o assistente.
6. Abrir o aplicativo e realizar login com credenciais válidas.

## Evidências do gate de instalação limpa (TASK-019)
- Evidências e checklist executado: [`docs/evidencias/TASK-019_validacao-vm-limpa.md`](../evidencias/TASK-019_validacao-vm-limpa.md).
- Registro da conclusão da task: [`tasks/TASK-019_gate-validacao-instalacao-limpa.md`](../../tasks/TASK-019_gate-validacao-instalacao-limpa.md).
