# Frontend — Loja Project

Aplicação React + Vite com TailwindCSS para interface do **Loja Project**.

## Stack

- React 18+
- Vite
- TypeScript
- TailwindCSS
- React Query
- React Router

## Como executar (desenvolvimento)

Antes de iniciar, configure a URL do backend:

```bash
cp .env.example .env
```

Defina `VITE_API_URL` no arquivo `.env` com a URL base do backend, sem barra no final.
Exemplo:

```env
VITE_API_URL=http://localhost:8000
```

Se `VITE_API_URL` não estiver definida, o frontend usa a mesma origem da aplicação carregada no navegador.

```bash
cd frontend
npm install
npm run dev
```

Aplicação disponível em `http://localhost:5173` (padrão Vite).

## Testes E2E

O frontend possui uma suite Playwright em `frontend/e2e/` com smoke tests
para login, dashboard, vendas e PDV.

Execucao local:

```bash
cd frontend
npm run test:e2e
```

Relatorio HTML:

```bash
cd frontend
npm run test:report
```

Observacao: a suite atual usa mocks de API para validar os fluxos principais
de interface. Ela reduz regressao de UI, mas nao substitui cenarios
integrados com backend real.

## Testes E2E Integrados

O projeto tambem possui um primeiro fluxo integrado real em
`frontend/e2e/pdv.integration.spec.ts`, cobrindo:

- login real via frontend
- consulta de produto em backend real
- finalizacao de venda no PDV
- validacao de baixa de estoque no backend

Execucao local:

```bash
cd frontend
npm run test:e2e:integrated
```

Comportamento da config integrada:

- sobe o backend em `http://127.0.0.1:8000`
- sobe o frontend em `http://127.0.0.1:5173`
- injeta `VITE_API_URL=http://127.0.0.1:8000` no Vite

Pre-requisitos:

- backend com dependencias instaladas
- `DATABASE_URL`, `JWT_SECRET` e `CORS_ORIGINS` validos para o backend
- banco acessivel para a aplicacao

Relatorio HTML do fluxo integrado:

```bash
cd frontend
npx playwright show-report playwright-report-integration
```

## Como buildar e instalar (produção)

### 1. Build

```powershell
npx vite build
npm run make
```

O instalador será gerado em:
```
out/make/squirrel.windows/x64/frontend-0.0.0 Setup.exe
```

### 2. Desinstalar versão antiga (se houver)

```powershell
Remove-Item -Recurse -Force "C:\Users\usuario\AppData\Local\LojaProject"
```

### 3. Instalar

```powershell
& "C:\Users\usuario\loja-project-\frontend\out\make\squirrel.windows\x64\frontend-0.0.0 Setup.exe"
```

> ⚠️ O Avast pode bloquear o executável por ser desconhecido. Caso isso aconteça, vá em **Avast → Proteção → Quarentena**, restaure o arquivo e adicione a pasta como exceção:
> `C:\Users\usuario\AppData\Local\LojaProject\`

### 4. Atalho na Área de Trabalho

Caso precise recriar o atalho:

```powershell
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('C:\Users\usuario\Desktop\Loja Project.lnk')
$Shortcut.TargetPath = 'C:\Users\usuario\AppData\Local\LojaProject\app-0.0.0\frontend.exe'
$Shortcut.WorkingDirectory = 'C:\Users\usuario\AppData\Local\LojaProject\app-0.0.0'
$Shortcut.Description = 'Loja Project'
$Shortcut.Save()
```

> ⚠️ O atalho deve apontar para `app-0.0.0\frontend.exe` e não para `frontend.exe` na raiz — este último é apenas o launcher do Squirrel.

## Autenticação

- A tela de login está em `src/pages/Login.tsx`.
- O login usa `POST /api/v1/users/token` (`application/x-www-form-urlencoded`), enviando:
  - `username` = email
  - `password` = senha
- O token JWT é salvo em `localStorage` por `src/utils/auth.ts`.
- Após autenticação, o frontend busca `GET /api/v1/users/me` para recuperar os dados do usuário.
- Rotas protegidas usam `PrivateRoute` e redirecionam para `/login` quando não autenticado.

## Observação importante

As regras de negócio devem permanecer no backend. O frontend deve atuar apenas como camada de apresentação e interação.
