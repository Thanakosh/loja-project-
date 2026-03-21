# Estrategia de Desenvolvimento - Loja Project

Este documento detalha o planejamento estrategico para a evolucao do sistema, focando em escalabilidade, modernizacao tecnica e valor de negocio.

## 1. Modernizacao Tecnica (Curto Prazo)
### Refatoracao de Dependencias
- **Pydantic v2:** Migrar todos os schemas para a versao 2 para melhorar a performance de validacao e serializacao.
- **FastAPI:** Atualizar para a versao mais recente para suporte a novos recursos assincronos.
- **Limpeza de Dependencias:** Remover pacotes legados como `python-magic` e `Mako` que nao sao essenciais ao nucleo.

### Arquitetura de Dados
- **Relacionamento Produto-Estoque:** Unificar as tabelas para que o estoque seja uma visao dinamica baseada em transacoes vinculadas ao ID do Produto.
- **Async Database (concluido):** A camada HTTP do backend e a infraestrutura principal de banco ja operam no padrao assincrono com `SQLAlchemy` async e `asyncpg`. Novos fluxos devem manter `AsyncSession`/`get_async_db` e evitar reintroduzir dependencias sync.

## 2. Expansao de Funcionalidades (Medio Prazo)
### Inteligencia Artificial & OCR - **Fase 2 (Planejada)**
- **Status atual (v2.1.0):** OCR/IA de imagens e PDFs esta desativado; o fluxo oficial ativo e importacao de NFe via XML.
- **Retomada futura:** OCR com processamento em segundo plano e filas persistentes quando a Fase 2 for iniciada.
- **Analise de tendencias (planejada):** uso de LLM apenas apos estabilizacao dos modulos core.

### Comunicacao & Vendas
- **Integracao WhatsApp:** Implementar servico de mensageria para envio de PDFs de orcamentos e notificacoes de estoque baixo.
- **Geracao de PDF:** Automatizar a criacao de documentos profissionais de orcamento.

## 3. Infraestrutura & DevOps
- **Docker Optimization:** Refinar o `Dockerfile` para builds multi-estagio, reduzindo o tamanho da imagem final.
- **Scripts de Automacao:** Substituir scripts `.ps1` por um `Makefile` unificado para facilitar o setup em qualquer sistema operacional.

## 4. Roadmap de Produto (ERP)
1. **Fase 1: Fundacao do Frontend (Desktop/Web)**
   - Desenvolvimento do app React + Electron + Vite
   - Configuracao do TailwindCSS e Design System
   - Integracao basica com backend FastAPI existente (login/dashboard)

2. **Fase 2: Core Business (Gestao Comercial)**
   - Cadastro completo de Fornecedores e Clientes
   - Gestao de Produtos avancada:
     - Categorias hierarquicas
     - Multiplos precos (custo, atacado, varejo)
     - Unidades de medida (metro, unidade, kg)

3. **Fase 3: Operacao de Loja (PDV)**
   - Frente de Caixa (PDV) com baixa automatica
   - Controle de Caixa (abertura/fechamento)
   - Orcamentos com conversao para venda

4. **Fase 4: Expansao e Fiscal**
   - Emissao de NF-e / NFC-e
   - Contas a Pagar e Receber
   - Integracao WhatsApp para orcamentos e notificacoes

## 5. Status do Roadmap (v2.1.0)
- **Ativo hoje:** XML de NFe, PDV com baixa automatica, orcamentos com conversao em venda, contas a receber com parcelamento, relatorios operacionais e dashboard com alertas.
- **Fase 2 - Planejada (sem prazo):** OCR/IA de imagens e PDFs (TASK-011 adiada).
- **Itens planejados (sem prazo):** controle de caixa diario, categorias hierarquicas, precificacao atacado/varejo.
