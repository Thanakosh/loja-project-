# Design System do Frontend

## Objetivo

Padronizar a camada visual do frontend com `shadcn/ui`, reduzindo componentes
ad-hoc e concentrando tokens de tema, estados visuais e padroes de composicao
em uma base reutilizavel.

## Base instalada

O design system foi inicializado no frontend com:

- alias `@/` para `frontend/src`
- tema semantico em `frontend/src/index.css`
- mapeamento dos tokens no `frontend/tailwind.config.js`
- configuracao do registry em `frontend/components.json`

Componentes `shadcn/ui` atualmente instalados:

- `alert`
- `alert-dialog`
- `badge`
- `button`
- `card`
- `dialog`
- `dropdown-menu`
- `input`
- `label`
- `popover`
- `select`
- `separator`
- `sheet`
- `skeleton`
- `sonner`
- `table`
- `tabs`
- `tooltip`

## Tokens de tema

Os componentes devem consumir classes semanticas como `bg-background`,
`text-foreground`, `bg-card`, `text-muted-foreground`, `border-border` e
`ring-ring`.

Tokens principais expostos por CSS variables:

- `background` e `foreground`
- `card` e `card-foreground`
- `popover` e `popover-foreground`
- `primary` e `primary-foreground`
- `secondary` e `secondary-foreground`
- `muted` e `muted-foreground`
- `accent` e `accent-foreground`
- `destructive` e `destructive-foreground`
- `border`, `input` e `ring`
- `radius`, `radius-md` e `radius-sm`

Direcao visual atual:

- base clara com tons neutros quentes
- cor primaria emerald
- tokens de risco com destaque em `destructive`
- suporte a modo dark mantido no mesmo conjunto semantico

## Padroes de uso

Use `Button`, `Input`, `Label` e `Alert` em formularios e estados de erro.

Use `Card` para blocos de pagina, KPIs, agrupamentos de conteudo e areas de
resumo como o dashboard.

Use `Dialog` para acoes bloqueantes e fluxos focados. Use `Sheet` quando o
contexto lateral fizer mais sentido do que interromper a pagina inteira.

Use `Select` para escolher um valor persistente de formulario. Use
`DropdownMenu` para menus de acao.

Use `Badge` para status, contagens e pequenos sinais visuais de estado.

Use `Skeleton` para loading perceptivel, `Separator` para divisao leve de
secoes, `Tabs` para alternancia de conteudo relacionado e `Tooltip` apenas
quando o rotulo nao puder ficar visivel.

O projeto continua com `react-hot-toast` para fluxos existentes. Nao remover ou
substituir sem validar todo o uso atual. O componente `sonner` fica disponivel
para novas telas, se a migracao de notificacoes for planejada depois.

## Como adicionar novos componentes

Adicionar um componente novo:

```bash
cd frontend
npx shadcn@latest add <componente>
```

Importar sempre pelo alias:

```tsx
import { Button } from "@/components/ui/button"
```

Ao introduzir um novo componente:

- prefira tokens semanticos em vez de cores hardcoded
- mantenha a regra de negocio no backend
- migre apenas a camada visual e de interacao
- valide com `npm run lint` e `npm run build`

## Paginas migradas nesta etapa

- `Login.tsx`
- `Dashboard.tsx`
