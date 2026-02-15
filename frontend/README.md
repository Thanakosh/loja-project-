# Frontend — Loja Project

Aplicação React + Vite com TailwindCSS para interface do **Loja Project**.

## Stack

- React 18+
- Vite
- TypeScript
- TailwindCSS
- React Query
- React Router

## Como executar

```bash
cd frontend
npm install
npm run dev
```

Aplicação disponível em `http://localhost:5173` (padrão Vite).

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
