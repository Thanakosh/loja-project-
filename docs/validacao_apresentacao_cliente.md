# Validação para apresentação ao cliente

Data: 2026-03-01

## 1) Suíte de testes

- Suíte backend executada com sucesso após ajuste em `.env.example`.
- Resultado atual: **135 passed**.

### Ajuste realizado

- Remoção da variável legada `OPENAI_KEY=` de `.env.example` para alinhar com a política atual do projeto e com os testes automatizados.

## 2) Funcionamento do roteiro de demonstração (smoke test)

Validação feita em ambiente local com:

- API FastAPI em `http://localhost:8000`
- Frontend Vite em `http://localhost:5173`
- Banco SQLite local para smoke test (`backend/ux_validation.db`)
- Usuário de demonstração: `admin@loja.com / admin`

### Endpoints-chave testados com autenticação

- `GET /api/v1/users/me` → 200
- `GET /api/v1/produtos/` → 200
- `GET /api/v1/clientes/` → 200
- `GET /api/v1/fornecedores/` → 200
- `GET /api/v1/orcamentos/` → 200
- `GET /api/v1/contas-receber/` → 200
- `GET /api/v1/vendas/` → 200
- `GET /api/v2/estoque/` → 200
- `GET /api/v2/estoque/alertas` → 200

Conclusão: o roteiro de navegação principal está tecnicamente funcional no backend para uma demo guiada.

## 3) UX e usabilidade

- Foi possível validar build do frontend com sucesso.
- A validação visual automatizada (Playwright) não foi concluída por falha do browser no ambiente de execução (crash/SIGSEGV), impedindo captura de screenshot.
- `eslint` apontou pendências de qualidade de frontend (tipagem `any` e hooks com dependências incompletas), que não bloqueiam build, mas impactam robustez e manutenção.

## 4) Executável para máquina do cliente

### 4.1 Situação atual

- O frontend é React + Vite e **não há configuração ativa de Electron/empacotamento** no `frontend/package.json` (sem scripts de build desktop).
- Portanto, **não está pronto hoje para entregar instalador `.exe`**.

### 4.2 Electron Builder vs Electron Forge (diferenças)

#### Electron Builder

- Foco forte em **empacotamento e distribuição**.
- Gera instaladores com mais opções avançadas para release (`.exe`, NSIS, assinatura, auto-update com provedores externos).
- Mais comum quando o objetivo é pipeline de release robusto e publicação recorrente.

**Prós:**
- Controle avançado de targets e instaladores.
- Ecossistema maduro para release corporativa.

**Contras:**
- Configuração inicial mais extensa.
- Curva maior para equipe sem experiência em empacotamento.

#### Electron Forge

- Foco em **experiência de desenvolvimento + empacotamento simplificado**.
- Fluxo mais guiado para iniciar app desktop rapidamente.
- Costuma ser ótimo para equipes pequenas validarem produto desktop com rapidez.

**Prós:**
- Setup inicial simples.
- Boa integração com fluxo de desenvolvimento.

**Contras:**
- Menos flexível que builder em cenários complexos de distribuição.
- Em releases corporativas avançadas, pode exigir ajustes extras.

### 4.3 Recomendação prática para este projeto

Como a necessidade imediata é validar venda com um cliente e entregar executável Windows com menor risco operacional:

- **Recomendação:** iniciar com **Electron Forge** para ganhar velocidade de implementação e reduzir complexidade inicial.
- Após validação comercial e primeiros clientes, migrar ou complementar com **Electron Builder** se houver necessidade de fluxo de release mais avançado (assinatura, auto-update e múltiplos canais).

## 5) Estratégia da API no desktop: local (serviço/container) vs remota

### 5.1 API local (serviço/container na máquina do cliente)

**Como funciona:**
- O executável desktop conversa com uma API rodando na própria máquina/rede local do cliente.

**Vantagens:**
- Independência de internet (com SQLite/Postgres local).
- Baixa latência local.
- Dados permanecem no ambiente do cliente.

**Desvantagens:**
- Instalação e suporte mais complexos (API, banco, backup).
- Atualizações de backend exigem processo controlado no cliente.
- Container local em Windows aumenta requisito técnico (Docker Desktop/licenciamento/recursos).

### 5.2 API remota (servidor hospedado)

**Como funciona:**
- O executável desktop é cliente da API publicada em nuvem/VPS.

**Vantagens:**
- Atualização centralizada do backend.
- Menor esforço de manutenção em cada máquina cliente.
- Melhor observabilidade e monitoramento operacional.

**Desvantagens:**
- Dependência de internet estável.
- Exige cuidados extras com segurança de tráfego, disponibilidade e LGPD.
- Custo recorrente de infraestrutura.

### 5.3 Recomendação para seu caso

Para apresentação comercial e evolução com menor complexidade de suporte:

- **Curto prazo (recomendado): API remota** em ambiente controlado (staging/prod leve), com o desktop apenas consumindo endpoints.
- **Plano B para cliente com operação offline:** evoluir para modo híbrido depois (cache/local queue + sincronização).
- **Não recomendo container local nesta primeira entrega comercial**, pois aumenta bastante risco de suporte na ponta.

## 6) Pipeline de build (Windows apenas)

Escopo solicitado: **somente Windows**.

### 6.1 Pipeline recomendado (GitHub Actions)

1. Trigger em tag/release (ex.: `v2.2.0-desktop.1`)
2. Runner `windows-latest`
3. Passos:
   - `npm ci`
   - `npm run build` (frontend)
   - `npm run make` ou `npm run package` (Electron Forge) **ou** `electron-builder`
4. Publicar artefato `.exe` (instalador)
5. (Opcional) assinatura de código quando já houver certificado

### 6.2 Entregáveis mínimos do pipeline

- Instalador `.exe`
- Checksum do arquivo (SHA256)
- Nota de versão com mudanças e requisitos

## 7) Teste em instalação limpa (obrigatório)

Você pediu explicitamente esse teste; recomendação: tratar como **gate obrigatório antes da entrega**.

### 7.1 Como executar

- Preparar VM Windows limpa (mesma versão do cliente, ex.: Windows 10/11 Pro).
- Sem Node/Python previamente instalados (simular ambiente real de usuário).
- Instalar somente o `.exe` gerado.

### 7.2 Checklist de aceite

1. Instalação concluída sem erro.
2. Aplicação abre e tela de login carrega.
3. Login com usuário válido funciona.
4. Navegação principal (Dashboard, Produtos, Estoque, PDV, Relatórios) abre sem travar.
5. Comunicação com API ocorre sem erro de CORS/SSL.
6. Fechar e reabrir app mantém comportamento esperado.
7. Desinstalação funciona sem resíduos críticos.

### 7.3 Critério de aprovação

- Só considerar “pronto para cliente” quando o checklist acima passar 100% na VM limpa.

## 8) Feedback final para apresentação comercial

- **Pronto para demo guiada** com dados de teste.
- **Ainda não pronto para distribuição como executável desktop** sem a sprint de desktop + pipeline + validação em instalação limpa.
- Prioridade sugerida: Electron Forge + API remota + pipeline Windows + teste em VM limpa como gate de release.
