# Validacao para apresentacao ao cliente

Data da validacao inicial: 2026-03-01

> Atualizacao de status (2026-03-26)
>
> Este documento registrou a avaliacao inicial da frente desktop. Desde entao,
> o estado do projeto mudou de forma relevante:
>
> - o frontend passou a ter empacotamento ativo com Electron Forge
> - o pipeline `windows-desktop-build` foi implementado
> - o gate de validacao em instalacao limpa foi documentado e concluido
> - a suite Playwright deixou de ser apenas expectativa e hoje cobre smoke tests
>   de frontend, alem de um fluxo integrado real de PDV
>
> O conteudo abaixo foi preservado como contexto da recomendacao inicial, mas as
> secoes 3, 4, 6 e 8 devem ser lidas considerando essa atualizacao.

## 1) Suite de testes

- Suite backend executada com sucesso apos ajuste em `.env.example`.
- Resultado atual: **135 passed**.

### Ajuste realizado

- Remocao da variavel legada `OPENAI_KEY=` de `.env.example` para alinhar com a politica atual do projeto e com os testes automatizados.

## 2) Funcionamento do roteiro de demonstracao (smoke test)

Validacao feita em ambiente local com:

- API FastAPI em `http://localhost:8000`
- Frontend Vite em `http://localhost:5173`
- Banco SQLite local para smoke test (`backend/ux_validation.db`)
- Usuario de demonstracao: `admin@loja.com / admin`

### Endpoints-chave testados com autenticacao

- `GET /api/v1/users/me`  200
- `GET /api/v1/produtos/`  200
- `GET /api/v1/clientes/`  200
- `GET /api/v1/fornecedores/`  200
- `GET /api/v1/orcamentos/`  200
- `GET /api/v1/contas-receber/`  200
- `GET /api/v1/vendas/`  200
- `GET /api/v2/estoque/`  200
- `GET /api/v2/estoque/alertas`  200

Conclusao: o roteiro de navegacao principal esta tecnicamente funcional no backend para uma demo guiada.

## 3) UX e usabilidade

- Foi possivel validar build do frontend com sucesso.
- A dificuldade inicial com Playwright nao representa mais o estado atual do
  projeto: o frontend ja possui smoke tests e um fluxo integrado real de PDV.
- `eslint` apontou pendencias de qualidade de frontend (tipagem `any` e hooks com dependencias incompletas), que nao bloqueiam build, mas impactam robustez e manutencao.

## 4) Executavel para maquina do cliente

### 4.1 Situacao atual

- O frontend continua em React + Vite, mas agora **ha configuracao ativa de
  Electron Forge** no `frontend/package.json`, com scripts de empacotamento
  desktop.
- O projeto **ja consegue gerar instalador `.exe` em Windows** e publicar o
  checksum SHA256 no pipeline de release.

### 4.2 Electron Builder vs Electron Forge (diferencas)

#### Electron Builder

- Foco forte em **empacotamento e distribuicao**.
- Gera instaladores com mais opcoes avancadas para release (`.exe`, NSIS, assinatura, auto-update com provedores externos).
- Mais comum quando o objetivo e pipeline de release robusto e publicacao recorrente.

**Pros:**
- Controle avancado de targets e instaladores.
- Ecossistema maduro para release corporativa.

**Contras:**
- Configuracao inicial mais extensa.
- Curva maior para equipe sem experiencia em empacotamento.

#### Electron Forge

- Foco em **experiencia de desenvolvimento + empacotamento simplificado**.
- Fluxo mais guiado para iniciar app desktop rapidamente.
- Costuma ser otimo para equipes pequenas validarem produto desktop com rapidez.

**Pros:**
- Setup inicial simples.
- Boa integracao com fluxo de desenvolvimento.

**Contras:**
- Menos flexivel que builder em cenarios complexos de distribuicao.
- Em releases corporativas avancadas, pode exigir ajustes extras.

### 4.3 Recomendacao pratica para este projeto

Como a necessidade imediata e validar venda com um cliente e entregar executavel Windows com menor risco operacional:

- **Recomendacao:** iniciar com **Electron Forge** para ganhar velocidade de implementacao e reduzir complexidade inicial.
- Apos validacao comercial e primeiros clientes, migrar ou complementar com **Electron Builder** se houver necessidade de fluxo de release mais avancado (assinatura, auto-update e multiplos canais).

## 5) Estrategia da API no desktop: local (servico/container) vs remota

### 5.1 API local (servico/container na maquina do cliente)

**Como funciona:**
- O executavel desktop conversa com uma API rodando na propria maquina/rede local do cliente.

**Vantagens:**
- Independencia de internet (com SQLite/Postgres local).
- Baixa latencia local.
- Dados permanecem no ambiente do cliente.

**Desvantagens:**
- Instalacao e suporte mais complexos (API, banco, backup).
- Atualizacoes de backend exigem processo controlado no cliente.
- Container local em Windows aumenta requisito tecnico (Docker Desktop/licenciamento/recursos).

### 5.2 API remota (servidor hospedado)

**Como funciona:**
- O executavel desktop e cliente da API publicada em nuvem/VPS.

**Vantagens:**
- Atualizacao centralizada do backend.
- Menor esforco de manutencao em cada maquina cliente.
- Melhor observabilidade e monitoramento operacional.

**Desvantagens:**
- Dependencia de internet estavel.
- Exige cuidados extras com seguranca de trafego, disponibilidade e LGPD.
- Custo recorrente de infraestrutura.

### 5.3 Recomendacao para seu caso

Para apresentacao comercial e evolucao com menor complexidade de suporte:

- **Curto prazo (recomendado): API remota** em ambiente controlado (staging/prod leve), com o desktop apenas consumindo endpoints.
- **Plano B para cliente com operacao offline:** evoluir para modo hibrido depois (cache/local queue + sincronizacao).
- **Nao recomendo container local nesta primeira entrega comercial**, pois aumenta bastante risco de suporte na ponta.

## 6) Pipeline de build (Windows apenas)

Escopo solicitado: **somente Windows**.

### 6.1 Pipeline recomendado (GitHub Actions)

Este pipeline deixou de ser apenas recomendacao e passou a existir no projeto:

1. Trigger em tag/release desktop
2. Runner `windows-latest`
3. Passos principais:
   - `npm ci`
   - `npm run build`
   - `npm run make`
4. Publicacao de instalador `.exe`
5. Publicacao de checksum SHA256

### 6.2 Entregaveis minimos do pipeline

- Instalador `.exe`
- Checksum do arquivo (SHA256)
- Nota de versao com mudancas e requisitos

## 7) Teste em instalacao limpa (obrigatorio)

Voce pediu explicitamente esse teste; recomendacao: tratar como **gate obrigatorio antes da entrega**.

### 7.1 Como executar

- Preparar VM Windows limpa (mesma versao do cliente, ex.: Windows 10/11 Pro).
- Sem Node/Python previamente instalados (simular ambiente real de usuario).
- Instalar somente o `.exe` gerado.

### 7.2 Checklist de aceite

1. Instalacao concluida sem erro.
2. Aplicacao abre e tela de login carrega.
3. Login com usuario valido funciona.
4. Navegacao principal (Dashboard, Produtos, Estoque, PDV, Relatorios) abre sem travar.
5. Comunicacao com API ocorre sem erro de CORS/SSL.
6. Fechar e reabrir app mantem comportamento esperado.
7. Desinstalacao funciona sem residuos criticos.

### 7.3 Criterio de aprovacao

- So considerar "pronto para cliente" quando o checklist acima passar 100% na VM limpa.

## 8) Feedback final para apresentacao comercial

- **Pronto para demo guiada** com dados de teste.
- **A trilha desktop minima ja foi estruturada**, incluindo empacotamento,
  pipeline Windows e validacao em instalacao limpa.
- O foco deixa de ser "viabilizar empacotamento" e passa a ser "amadurecer
  release e cobertura integrada real".
- Continua recomendada a estrategia de **API remota** para apresentacao
  comercial e operacao inicial com menor risco de suporte.
