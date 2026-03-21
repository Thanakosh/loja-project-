# Auditoria de Segredos no Historico Git

**Task:** TASK-036  
**Data:** 2026-03-21  
**Branch de trabalho:** `docs/auditoria-git-segredos`  
**Status final:** concluida

## Escopo

Auditoria do historico Git para verificar:

- arquivos `.env`
- bancos SQLite locais (`test.db`, `loja.db`)
- arquivos sensiveis (`*.key`, `*.pem`, `*.p12`)
- ocorrencias de strings de configuracao como `JWT_SECRET=`, `DATABASE_URL=` e `SECRET_KEY`

Esta task e apenas de leitura, analise e documentacao. Nenhuma reescrita de historico foi executada.

## Comandos utilizados

```powershell
git log --all --full-history -- .env
git log --all --full-history -- "*.env"
git log --all --full-history -- backend/.env
git log --all --full-history -- test.db
git log --all --full-history -- loja.db
git log --all --full-history -- "*.key"
git log --all --full-history -- "*.pem"
git log --all --full-history -- "*.p12"
git log --all -S "JWT_SECRET=" --oneline
git log --all -S "DATABASE_URL=" --oneline
git log --all -S "SECRET_KEY" --oneline
```

## Resultado por verificacao

### 1. Arquivos `.env`

| Consulta | Resultado |
|---------|-----------|
| `.env` na raiz | nenhum commit encontrado |
| `*.env` no repositorio | nenhum commit encontrado |
| `backend/.env` | nenhum commit encontrado |

Conclusao: nao encontrei evidencias de `.env` versionado no historico Git.

### 2. Bancos SQLite no historico

| Arquivo | Resultado |
|---------|-----------|
| `test.db` | encontrado no historico |
| `loja.db` | nenhum commit encontrado |

Evidencias confirmadas para `test.db`:

- commit `32f4089` (`chore: limpa arquivos obsoletos e reorganiza testes`) inclui `test.db`
- commit `437c1c2` (`fix: Correcoes de bugs identificados durante os testes da v2.0`) inclui `test.db`

Conclusao: o historico nao esta limpo para bancos locais, porque `test.db` foi commitado no passado.

### 3. Chaves e certificados

| Padrao | Resultado |
|-------|-----------|
| `*.key` | nenhum commit encontrado |
| `*.pem` | nenhum commit encontrado |
| `*.p12` | nenhum commit encontrado |

Conclusao: nao encontrei evidencias de arquivos de chave privada ou certificado no historico.

### 4. Strings sensiveis ou de configuracao

| Busca | Resultado |
|------|-----------|
| `JWT_SECRET=` | ha ocorrencias no historico |
| `DATABASE_URL=` | ha ocorrencias no historico |
| `SECRET_KEY` | ha ocorrencias no historico |

Observacao importante: a presenca dessas strings no historico nao prova, por si so, exposicao de credenciais reais. Parte dessas ocorrencias vem de arquivos versionados de exemplo, configuracao ou testes. Ainda assim, a afirmacao "nenhuma ocorrencia" seria incorreta.

## Estado atual dos arquivos locais relevantes

### `.env.example`

O repositorio possui valores de exemplo e placeholders, incluindo:

- `DATABASE_URL=sqlite:///./test.db`
- `JWT_SECRET=dev-local-secret-change-in-production-abc123`
- `POSTGRES_PASSWORD=loja_pass`

### `backend/.env`

O arquivo local atual contem:

- `DATABASE_URL=sqlite:///./loja.db`
- `JWT_SECRET=dev-local-secret-change-in-production-abc123`
- `FASTAPI_USERS_SECRET=dev-local-secret-change-in-production-abc123`

Isso reforca que o ambiente local ainda usa um segredo fraco/de placeholder e exige troca antes de qualquer deploy.

## Veredicto

Resultado consolidado:

- `.env` nao apareceu no historico
- `test.db` apareceu no historico
- `loja.db` nao apareceu
- `*.key`, `*.pem` e `*.p12` nao apareceram
- ha ocorrencias no historico para `JWT_SECRET=`, `DATABASE_URL=` e `SECRET_KEY`
- nao encontrei, nesta auditoria, evidencia objetiva de uma credencial real exposta em `.env` commitado

Veredicto final:

O historico Git nao pode ser descrito como totalmente limpo, porque `test.db` foi versionado no passado e ha strings sensiveis/de configuracao no historico. Por outro lado, nao encontrei evidencias de `.env` commitado nem de chaves/certificados privados versionados.

## Acoes recomendadas

1. Trocar `JWT_SECRET` e `FASTAPI_USERS_SECRET` locais antes de qualquer deploy:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. Manter `.env`, `*.db` e artefatos locais protegidos no `.gitignore`.

3. Avaliar se o historico de `test.db` exige saneamento. Se a decisao for remover, isso deve ser feito com coordenacao do time usando reescrita de historico.

4. Adicionar verificacao automatica com `gitleaks` ou `detect-secrets` no fluxo de desenvolvimento.

5. Revisar arquivos versionados de exemplo para garantir que placeholders sejam sempre explicitamente nao produtivos.
