# Estratégia de Desenvolvimento - Loja Project

Este documento detalha o planejamento estratégico para a evolução do sistema, focando em escalabilidade, modernização técnica e valor de negócio.

## 1. Modernização Técnica (Curto Prazo)
### Refatoração de Dependências
- **Pydantic v2:** Migrar todos os schemas para a versão 2 para melhorar a performance de validação e serialização.
- **FastAPI:** Atualizar para a versão mais recente para suporte a novos recursos assíncronos.
- **Limpeza de Dependências:** Remover pacotes legados como `python-magic` e `Mako` que não são essenciais ao núcleo.

### Arquitetura de Dados
- **Relacionamento Produto-Estoque:** Unificar as tabelas para que o estoque seja uma visão dinâmica baseada em transações vinculadas ao ID do Produto.
- **Async Database:** Migrar as chamadas de banco de dados para o padrão totalmente assíncrono usando `SQLAlchemy` e `asyncpg`.

## 2. Expansão de Funcionalidades (Médio Prazo)
### Inteligência Artificial & OCR — **Fase 2 (Planejada)**
- **Status atual (v2.1.0):** OCR/IA de imagens e PDFs está desativado; o fluxo oficial ativo é importação de NFe via XML.
- **Retomada futura:** OCR com processamento em segundo plano e filas persistentes quando a Fase 2 for iniciada.
- **Análise de tendências (planejada):** uso de LLM apenas após estabilização dos módulos core.

### Comunicação & Vendas
- **Integração WhatsApp:** Implementar serviço de mensageria para envio de PDFs de orçamentos e notificações de estoque baixo.
- **Geração de PDF:** Automatizar a criação de documentos profissionais de orçamento.

## 3. Infraestrutura & DevOps
- **Docker Optimization:** Refinar o `Dockerfile` para builds multi-estágio, reduzindo o tamanho da imagem final.
- **Scripts de Automação:** Substituir scripts `.ps1` por um `Makefile` unificado para facilitar o setup em qualquer sistema operacional.

## 4. Roadmap de Produto (ERP)
1. **Fase 1: Fundação do Frontend (Desktop/Web)**
   - Desenvolvimento do app React + Electron + Vite
   - Configuração do TailwindCSS e Design System
   - Integração básica com backend FastAPI existente (login/dashboard)

2. **Fase 2: Core Business (Gestão Comercial)**
   - Cadastro completo de Fornecedores e Clientes
   - Gestão de Produtos avançada:
     - Categorias hierárquicas
     - Múltiplos preços (custo, atacado, varejo)
     - Unidades de medida (metro, unidade, kg)

3. **Fase 3: Operação de Loja (PDV)**
   - Frente de Caixa (PDV) com baixa automática
   - Controle de Caixa (abertura/fechamento)
   - Orçamentos com conversão para venda

4. **Fase 4: Expansão e Fiscal**
   - Emissão de NF-e / NFC-e
   - Contas a Pagar e Receber
   - Integração WhatsApp para orçamentos e notificações

## 5. Status do Roadmap (v2.1.0)
- **Ativo hoje:** XML de NFe, PDV com baixa automática, orçamentos com conversão em venda, contas a receber com parcelamento, relatórios operacionais e dashboard com alertas.
- **Fase 2 — Planejada (sem prazo):** OCR/IA de imagens e PDFs (TASK-011 adiada).
- **Itens planejados (sem prazo):** controle de caixa diário, categorias hierárquicas, precificação atacado/varejo.
