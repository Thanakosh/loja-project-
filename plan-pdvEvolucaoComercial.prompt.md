## Plan: Evolução PDV Comercial (DRAFT)

Vamos entregar em fases curtas, começando pelo que gera valor imediato no balcão (agilidade no PDV e comprovante em PDF), sem duplicar regra de negócio no frontend. As decisões já alinhadas: autorização de terceiros será híbrida (cadastro + registro por venda com histórico), nenhum campo obrigatório inicialmente além de observação livre, código de barras no MVP com 1 código por produto, feedback de clique com realce + toast, e impressão via PDF no MVP. Para desconto progressivo, a implementação seguirá padrão de mercado com política por produto/volume e governança de margem/comissão no backend, preservando rastreabilidade para vendas a prazo.

**Steps**
1. Mapear contratos atuais e preparar ajustes de schema/API para PDV e clientes em backend/app/schemas/pdv.py, backend/app/schemas/cliente.py, backend/app/api/v1/pdv.py, backend/app/api/v1/clientes.py, mantendo `POST /api/v1/pdv/venda` como ponto central de regra.
2. Implementar MVP de código de barras (1 por produto): adicionar campo e índice em produto via migração em migrations/versions, atualizar backend/app/models/produto.py, backend/app/schemas/produto.py, e busca dedicada em backend/app/api/v1/produto.py para lookup exato.
3. Evoluir cadastro de cliente com histórico de observações/autorização (ordem da mais recente para a mais antiga) e snapshot na venda a prazo em backend/app/models/cliente.py, backend/app/models/venda.py, backend/app/services/pdv_service.py, garantindo auditoria do autorizador no fechamento.
4. Ajustar UX do PDV para decremento com feedback visual no clique (realce de linha + toast) e fluxo de bipagem no foco principal em frontend/src/pages/PDV.tsx, com comportamento otimista e validação final pelo backend.
5. Implementar comprovante de venda em PDF no pós-venda: gerar endpoint PDF por venda (ex.: `/api/v1/pdv/venda/{id}/comprovante`) e ação de download/impressão no frontend, reaproveitando padrões de backend/app/services/pdf_service.py.
6. Criar motor de desconto progressivo por produto/volume no backend (padrão mercado): política por faixas, limites por margem e registro de motivo/autorização em backend/app/services/pdv_service.py, com estrutura de faixas em nova tabela/migração se necessário.
7. Integrar impacto em venda a prazo e contas a receber, assegurando que autorização/snapshot apareça no financeiro em backend/app/models/conta_receber.py e backend/app/api/v1/contas_receber.py.
8. Cobrir testes unitários/API/e2e: expandir backend/tests/test_pdv.py, backend/tests/test_clientes.py, e frontend/e2e/pdv.spec.ts para barras, decremento-feedback, autorização de terceiro, desconto progressivo e impressão em PDF.

**Verification**
- Backend: executar `pytest tests/test_pdv.py tests/test_clientes.py -v` em backend/tests.
- Frontend/E2E: executar suíte do PDV em frontend/e2e/pdv.spec.ts cobrindo bipagem, decremento e comprovante em PDF.
- Validação manual: fluxo completo no PDV (produto por barras → venda a prazo com observação/autorização → geração de comprovante em PDF).

**Decisions**
- Autorização de terceiros: modelo híbrido (cadastro + por venda) com histórico ordenado por recência.
- Dados obrigatórios do terceiro no MVP: nenhum; observação livre como principal.
- Código de barras no MVP: 1 código por produto.
- Feedback de clique no PDV: realce visual + toast.
- Impressão no MVP: comprovante em PDF.
- Desconto progressivo: regra backend por produto/volume com trilha de auditoria e limite por política comercial.