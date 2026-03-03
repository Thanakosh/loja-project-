"""Testes para o motor de auditoria fiscal (engine.py + audit_service.py) e endpoint validate-note."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.fiscal.engine import (
    VERSAO_ENGINE_REGRAS,
    AuditFinding,
    executar_auditoria_regras,
)
from app.ai.audit_service import (
    VERSAO_AUDIT_SERVICE,
    auditar_nota_fiscal,
)
from app.schemas.fiscal_payload import FiscalItemPayload, NotaFiscalPayloadNormalizado


# ─── Helpers ───


def _make_item(**overrides) -> FiscalItemPayload:
    """Cria um FiscalItemPayload com defaults razoáveis."""
    defaults = dict(
        sequencia=1,
        descricao="Produto Teste",
        quantidade=Decimal("10"),
        unidade_comercial="UN",
        valor_unitario=Decimal("50.00"),
        valor_total_item=Decimal("500.00"),
        ncm="84713012",
    )
    defaults.update(overrides)
    return FiscalItemPayload.model_validate(defaults)


def _make_nota(itens: list[FiscalItemPayload] | None = None) -> NotaFiscalPayloadNormalizado:
    """Cria uma nota normalizada com defaults."""
    if itens is None:
        itens = [_make_item()]
    return NotaFiscalPayloadNormalizado(
        versao_payload="1.0.0",
        fornecedor_nome="Fornecedor Teste",
        fornecedor_cnpj="12345678000199",
        valor_total_nota=sum(i.valor_total_item for i in itens),
        itens=itens,
    )


# ═══════════════════════════════════════════
# Testes unitários — Engine de regras
# ═══════════════════════════════════════════


class TestEngineRegras:
    def test_nota_limpa_sem_findings(self):
        """Nota com CST válido e alíquota normal não deve gerar findings."""
        item = _make_item(cst="00", icms_aliquota=Decimal("18.0"), icms_base_calculo=Decimal("500.0"))
        nota = _make_nota([item])
        result = executar_auditoria_regras(nota)
        assert len(result.findings) == 0
        assert result.total_erros == 0
        assert result.total_alertas == 0

    def test_cst_e_csosn_coexistentes_gera_erro(self):
        """CST e CSOSN simultâneos devem gerar finding de erro."""
        item = _make_item(cst="00", csosn="102")
        nota = _make_nota([item])
        result = executar_auditoria_regras(nota)
        assert result.total_erros >= 1
        regras = [f.regra for f in result.findings]
        assert "cst_csosn_coexistentes" in regras

    def test_cst_invalido_gera_erro(self):
        """CST desconhecido deve gerar finding de erro."""
        item = _make_item(cst="99")
        nota = _make_nota([item])
        result = executar_auditoria_regras(nota)
        regras = [f.regra for f in result.findings]
        assert "cst_invalido" in regras

    def test_csosn_invalido_gera_erro(self):
        """CSOSN desconhecido deve gerar finding de erro."""
        item = _make_item(csosn="999")
        nota = _make_nota([item])
        result = executar_auditoria_regras(nota)
        regras = [f.regra for f in result.findings]
        assert "csosn_invalido" in regras

    def test_aliquota_acima_do_teto_gera_alerta(self):
        """Alíquota acima de 35% deve gerar alerta."""
        item = _make_item(icms_aliquota=Decimal("50.0"))
        nota = _make_nota([item])
        result = executar_auditoria_regras(nota)
        assert result.total_alertas >= 1
        regras = [f.regra for f in result.findings]
        assert "aliquota_fora_faixa" in regras

    def test_aliquota_negativa_gera_alerta(self):
        """Alíquota negativa deve gerar alerta."""
        item = _make_item(icms_aliquota=Decimal("-5.0"))
        nota = _make_nota([item])
        result = executar_auditoria_regras(nota)
        regras = [f.regra for f in result.findings]
        assert "aliquota_fora_faixa" in regras

    def test_outlier_preco_mesmo_ncm_gera_alerta(self):
        """Itens com mesmo NCM e preço com variação > 3x devem gerar alerta."""
        item1 = _make_item(sequencia=1, ncm="84713012", valor_unitario=Decimal("10.00"), valor_total_item=Decimal("100.00"))
        item2 = _make_item(sequencia=2, ncm="84713012", valor_unitario=Decimal("50.00"), valor_total_item=Decimal("500.00"))
        nota = _make_nota([item1, item2])
        result = executar_auditoria_regras(nota)
        regras = [f.regra for f in result.findings]
        assert "outlier_preco_ncm" in regras

    def test_ncm_diferente_nao_gera_outlier(self):
        """Itens com NCMs diferentes não devem gerar outlier entre si."""
        item1 = _make_item(sequencia=1, ncm="84713012", valor_unitario=Decimal("10.00"), valor_total_item=Decimal("100.00"))
        item2 = _make_item(sequencia=2, ncm="99999999", valor_unitario=Decimal("50.00"), valor_total_item=Decimal("500.00"))
        nota = _make_nota([item1, item2])
        result = executar_auditoria_regras(nota)
        regras = [f.regra for f in result.findings]
        assert "outlier_preco_ncm" not in regras

    def test_icms_base_sem_aliquota_gera_alerta(self):
        """Base de cálculo presente sem alíquota gera alerta."""
        item = _make_item(icms_base_calculo=Decimal("500.0"), icms_aliquota=None)
        nota = _make_nota([item])
        result = executar_auditoria_regras(nota)
        regras = [f.regra for f in result.findings]
        assert "icms_base_sem_aliquota" in regras

    def test_versao_engine_presente(self):
        nota = _make_nota()
        result = executar_auditoria_regras(nota)
        assert result.versao_engine == VERSAO_ENGINE_REGRAS


# ═══════════════════════════════════════════
# Testes unitários — Audit Service (score + classificação)
# ═══════════════════════════════════════════


class TestAuditService:
    def test_nota_limpa_classifica_risco_baixo(self):
        """Nota sem problemas deve ser classificada como risco baixo."""
        item = _make_item(cst="00", icms_aliquota=Decimal("18.0"), icms_base_calculo=Decimal("500.0"))
        nota = _make_nota([item])
        result = auditar_nota_fiscal(nota)
        assert result.classificacao == "baixo"
        assert result.score == 0.0
        assert result.total_erros == 0
        assert result.confianca >= 0.7

    def test_nota_com_erro_critico_classifica_risco_alto(self):
        """Nota com múltiplos erros deve atingir risco alto."""
        # 2 erros (CST+CSOSN coexistentes + CST inválido em outro item) = 60+ pontos
        item1 = _make_item(sequencia=1, cst="00", csosn="102")  # cst_csosn_coexistentes (30)
        item2 = _make_item(sequencia=2, cst="99")  # cst_invalido (30)
        nota = _make_nota([item1, item2])
        result = auditar_nota_fiscal(nota)
        assert result.classificacao == "alto"
        assert result.score >= 50.0

    def test_nota_com_alertas_classifica_risco_medio(self):
        """Nota com alertas mas sem erros pode atingir risco médio."""
        # 3 alertas = 30 pontos → médio (>= 20, < 50)
        # icms_base_calculo evita disparo extra de icms_aliquota_sem_base
        item1 = _make_item(sequencia=1, icms_aliquota=Decimal("50.0"), icms_base_calculo=Decimal("100.0"))  # alerta fora faixa
        item2 = _make_item(sequencia=2, icms_base_calculo=Decimal("100.0"), icms_aliquota=None)  # base sem aliquota
        item3 = _make_item(sequencia=3, icms_aliquota=Decimal("40.0"), icms_base_calculo=Decimal("100.0"))  # alerta fora faixa
        nota = _make_nota([item1, item2, item3])
        result = auditar_nota_fiscal(nota)
        assert result.classificacao == "medio"
        assert result.total_alertas >= 2

    def test_explicacao_contem_regras_acionadas(self):
        """Explicação textual deve citar as regras que foram acionadas."""
        item = _make_item(cst="00", csosn="102")
        nota = _make_nota([item])
        result = auditar_nota_fiscal(nota)
        assert "cst_csosn_coexistentes" in result.explicacao

    def test_fatores_correspondem_aos_findings(self):
        """Cada finding deve gerar um fator correspondente."""
        item = _make_item(icms_aliquota=Decimal("50.0"))  # 1 alerta
        nota = _make_nota([item])
        result = auditar_nota_fiscal(nota)
        assert len(result.fatores) >= 1
        assert result.fatores[0].regra == "aliquota_fora_faixa"
        assert result.fatores[0].peso > 0

    def test_versoes_presentes_no_resultado(self):
        nota = _make_nota()
        result = auditar_nota_fiscal(nota)
        assert result.versao_engine == VERSAO_ENGINE_REGRAS
        assert result.versao_service == VERSAO_AUDIT_SERVICE


# ═══════════════════════════════════════════
# Testes de integração — Endpoint
# ═══════════════════════════════════════════


class TestFiscalAuditEndpoint:
    ENDPOINT = "/api/v1/fiscal-ai/validate-note"

    def _payload_limpo(self) -> dict:
        return {
            "fornecedor_nome": "Fornecedor Teste",
            "fornecedor_cnpj": "12345678000199",
            "itens": [
                {
                    "descricao": "Produto A",
                    "quantidade": 10,
                    "valor_unitario": 50.0,
                    "cst": "00",
                    "icms_base_calculo": 500.0,
                    "icms_aliquota": 18.0,
                    "icms_valor": 90.0,
                }
            ],
        }

    def _payload_com_erros(self) -> dict:
        return {
            "fornecedor_nome": "Fornecedor Problemático",
            "itens": [
                {
                    "descricao": "Produto B",
                    "quantidade": 5,
                    "valor_unitario": 100.0,
                    "cst": "00",
                    "csosn": "102",  # CST e CSOSN simultâneos → erro
                },
                {
                    "descricao": "Produto C",
                    "quantidade": 3,
                    "valor_unitario": 200.0,
                    "cst": "99",  # CST inválido → erro
                    "icms_aliquota": 50.0,  # fora de faixa → alerta
                },
            ],
        }

    def test_validate_note_retorna_200_nota_limpa(self, client: TestClient, auth_headers: dict):
        resp = client.post(self.ENDPOINT, json=self._payload_limpo(), headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["classificacao"] == "baixo"
        assert data["total_erros"] == 0
        assert data["versao_engine"] == VERSAO_ENGINE_REGRAS
        assert data["versao_service"] == VERSAO_AUDIT_SERVICE

    def test_validate_note_retorna_200_nota_com_erros(self, client: TestClient, auth_headers: dict):
        resp = client.post(self.ENDPOINT, json=self._payload_com_erros(), headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["classificacao"] in ("medio", "alto")
        assert data["total_erros"] >= 1
        assert len(data["fatores"]) >= 1
        assert data["score"] > 0

    def test_validate_note_contrato_completo(self, client: TestClient, auth_headers: dict):
        """Verifica que todos os campos do contrato estão presentes."""
        resp = client.post(self.ENDPOINT, json=self._payload_limpo(), headers=auth_headers)
        data = resp.json()
        campos_obrigatorios = {
            "classificacao", "confianca", "score", "explicacao",
            "fatores", "total_erros", "total_alertas",
            "versao_engine", "versao_service",
        }
        assert campos_obrigatorios.issubset(data.keys())

    def test_validate_note_sem_auth_retorna_401(self, client: TestClient):
        resp = client.post(self.ENDPOINT, json=self._payload_limpo())
        assert resp.status_code == 401

    def test_validate_note_payload_invalido_retorna_422(self, client: TestClient, auth_headers: dict):
        resp = client.post(self.ENDPOINT, json={"itens": []}, headers=auth_headers)
        assert resp.status_code == 422
