---
task_id: TASK-004
title: "Criar Dockerfile e docker-compose.yml"
priority: baixa
scope: raiz do projeto
branch: chore/docker-setup
commit_message: "chore(infra): adiciona Dockerfile e docker-compose.yml"
estimated_effort: 20 minutos
status: concluida
---

# TASK-004: Criar Dockerfile e docker-compose.yml

## Contexto
O projeto nao possui containerizacao. Adicionar Docker facilita deploy, onboarding
de novos desenvolvedores e testes em ambientes isolados. Esta listado no roadmap
de curto prazo do README.md.

## Arquivos a criar

### 1. `Dockerfile` (raiz do projeto)
```dockerfile
# Multi-stage build para imagem otimizada
FROM python:3.12-slim AS base

# Variaveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Instalar dependencias de sistema (necessarias para psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo da aplicacao
COPY backend/app ./app
COPY alembic.ini .
COPY migrations ./migrations

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/ping')" || exit 1

# Comando de inicializacao
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. `docker-compose.yml` (raiz do projeto)
```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    container_name: loja-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-loja_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-loja_pass}
      POSTGRES_DB: ${POSTGRES_DB:-loja_db}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-loja_user}"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: loja-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-loja_user}:${POSTGRES_PASSWORD:-loja_pass}@db:5432/${POSTGRES_DB:-loja_db}
      JWT_SECRET: ${JWT_SECRET:-change-me-in-production}
      JWT_ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 30
      OLLAMA_URL: ${OLLAMA_URL:-http://host.docker.internal:11434}
      DEBUG: ${DEBUG:-false}
      CORS_ORIGINS: ${CORS_ORIGINS:-["http://localhost:3000"]}
    depends_on:
      db:
        condition: service_healthy
    command: >
      sh -c "
        alembic upgrade head &&
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
      "

  # Ollama (opcional, descomente se quiser rodar LLM local)
  # ollama:
  #   image: ollama/ollama:latest
  #   container_name: loja-ollama
  #   ports:
  #     - "11434:11434"
  #   volumes:
  #     - ollama_data:/root/.ollama

volumes:
  postgres_data:
  # ollama_data:
```

### 3. `.dockerignore` (raiz do projeto)
```
.git
.gitignore
__pycache__
*.pyc
*.pyo
.pytest_cache
.env
test.db
*.egg-info
dist
build
venv
.venv
node_modules
checkpoints
docs
*.md
!requirements*.txt
backend/.pytest_cache
backend/tests
```

### 4. Atualizar `.env.example` - adicionar variaveis Docker
Adicionar ao final do `.env.example` existente:
```env
# Docker / PostgreSQL
POSTGRES_USER=loja_user
POSTGRES_PASSWORD=loja_pass
POSTGRES_DB=loja_db
```

## Passos
1. Criar branch `chore/docker-setup`
2. Criar `Dockerfile` na raiz do projeto
3. Criar `docker-compose.yml` na raiz
4. Criar `.dockerignore` na raiz
5. Atualizar `.env.example` com variaveis do Docker
6. Testar build: `docker compose build`
7. Testar execucao: `docker compose up -d`
8. Verificar health: `curl http://localhost:8000/ping`
9. Verificar logs: `docker compose logs api`
10. Commit seguindo Conventional Commits

## Criterios de aceite
- [ ] `docker compose build` roda sem erros
- [ ] `docker compose up` sobe api + postgres
- [ ] API responde em `http://localhost:8000/ping`
- [ ] Migracoes Alembic rodam automaticamente no startup
- [ ] Banco de dados persiste entre reinicializacoes (volume)
- [ ] `.env.example` atualizado com variaveis Docker
- [ ] `.dockerignore` exclui arquivos desnecessarios

## Notas
- O Dockerfile usa `python:3.12-slim` por ser leve e compativel
- O compose usa `depends_on` com health check para garantir que o DB esta pronto
- Ollama esta comentado por padrao (e opcional)
- Em producao, remover `--reload` do uvicorn e usar `gunicorn`
- NAO commitar `.env`, apenas `.env.example`

## Atualizacao de status
-  `Dockerfile` e `docker-compose.yml` ja versionados na raiz
-  Tarefa mantida como referencia de operacao e onboarding
