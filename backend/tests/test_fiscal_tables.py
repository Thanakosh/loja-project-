"""Testes das tabelas fiscais oficiais e validador cruzado."""

from decimal import Decimal

import pytest

from app.fiscal.tables.cst_icms import (
    CST_ICMS,
    is_valid_cst_icms,
    get_cst_icms_descricao,
)
from app.fiscal.tables.csosn import (
    CSOSN,
    is_valid_csosn,
    get_csosn_descricao,
)
from app.fiscal.tables.cfop import (
    CFOP,
    is_valid_cfop,
    get_cfop_descricao,
    cfop_direction,
    cfop_scope,
    cfop_is_devolucao,
    cfop_is_transferencia,
    cfop_is_st,
)
from app.fiscal.tables.cst_pis_cofins import (
    CST_PIS_COFINS,
    is_valid_cst_pis_cofins,
    get_cst_pis_cofins_descricao,
    is_saida,
    is_entrada_com_credito,
    is_entrada_sem_credito,
)
from app.fiscal.tables.ncm import (
    NCM_VAREJO,
    is_valid_ncm_format,
    normalize_ncm,
    get_ncm_descricao,
    format_ncm,
    search_ncm,
)
from app.fiscal.tables.cest import (
    CEST_VAREJO,
    SEGMENTOS_CEST,
    is_valid_cest_format,
    normalize_cest,
    get_cest_descricao,
    format_cest,
    get_segmento,
    search_cest,
)
from app.fiscal.tables.aliquotas_uf import (
    ALIQUOTA_INTERNA,
    get_aliquota_interna,
    get_aliquota_interestadual,
    calcular_difal,
)
from app.fiscal.cross_validator import (
    CrossFinding,
    validar_nota_cruzado,
)
from app.schemas.fiscal_payload import (
    FiscalItemPayload,
    NotaFiscalPayloadNormalizado,
)


# ═══════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════


def _make_item(**kwargs) -> FiscalItemPayload:
    """Cria um FiscalItemPayload com defaults razoáveis."""
    defaults = {
        "sequencia": 1,
        "descricao": "Produto teste",
        "quantidade": Decimal("1"),
        "unidade_comercial": "UN",
        "valor_unitario": Decimal("10.00"),
        "valor_total_item": Decimal("10.00"),
    }
    defaults.update(kwargs)
    return FiscalItemPayload(**defaults)


def _make_nota(itens=None, **kwargs) -> NotaFiscalPayloadNormalizado:
    """Cria uma nota com defaults razoáveis."""
    if itens is None:
        itens = [_make_item()]
    defaults = {
        "versao_payload": "1.0",
        "fornecedor_nome": "Fornecedor Teste LTDA",
        "valor_total_nota": sum(i.valor_total_item for i in itens),
        "itens": itens,
    }
    defaults.update(kwargs)
    return NotaFiscalPayloadNormalizado(**defaults)


# ═══════════════════════════════════════
#  CST ICMS
# ═══════════════════════════════════════


class TestCstIcms:
    def test_tabela_tem_11_codigos(self):
        assert len(CST_ICMS) == 11

    def test_codigos_validos(self):
        for code in ["00", "10", "20", "30", "40", "41", "50", "51", "60", "70", "90"]:
            assert is_valid_cst_icms(code), f"{code} deveria ser válido"

    def test_codigo_invalido(self):
        assert not is_valid_cst_icms("99")
        assert not is_valid_cst_icms("ABC")
        assert not is_valid_cst_icms("")

    def test_descricao(self):
        desc = get_cst_icms_descricao("00")
        assert desc is not None
        assert "integral" in desc.lower() or "integralmente" in desc.lower()

    def test_descricao_inexistente(self):
        assert get_cst_icms_descricao("99") is None


# ═══════════════════════════════════════
#  CSOSN
# ═══════════════════════════════════════


class TestCsosn:
    def test_tabela_tem_10_codigos(self):
        assert len(CSOSN) == 10

    def test_codigos_validos(self):
        for code in ["101", "102", "103", "201", "202", "203", "300", "400", "500", "900"]:
            assert is_valid_csosn(code), f"{code} deveria ser válido"

    def test_codigo_invalido(self):
        assert not is_valid_csosn("100")
        assert not is_valid_csosn("999")

    def test_descricao(self):
        desc = get_csosn_descricao("101")
        assert desc is not None


# ═══════════════════════════════════════
#  CFOP
# ═══════════════════════════════════════


class TestCfop:
    def test_tabela_nao_vazia(self):
        assert len(CFOP) > 100

    def test_cfop_validos(self):
        for code in ["1102", "5102", "5405", "6102", "2102"]:
            assert is_valid_cfop(code), f"{code} deveria ser válido"

    def test_cfop_invalido(self):
        assert not is_valid_cfop("0000")
        assert not is_valid_cfop("9999")
        assert not is_valid_cfop("ABC")

    def test_descricao(self):
        desc = get_cfop_descricao("5102")
        assert desc is not None

    def test_direction_entrada(self):
        assert cfop_direction("1102") == "entrada"
        assert cfop_direction("2102") == "entrada"
        assert cfop_direction("3102") == "entrada"

    def test_direction_saida(self):
        assert cfop_direction("5102") == "saida"
        assert cfop_direction("6102") == "saida"
        assert cfop_direction("7102") == "saida"

    def test_scope(self):
        assert cfop_scope("1102") == "estadual"
        assert cfop_scope("2102") == "interestadual"
        assert cfop_scope("3102") == "exterior"

    def test_devolucao(self):
        assert cfop_is_devolucao("1201") is True
        assert cfop_is_devolucao("5102") is False

    def test_transferencia(self):
        assert cfop_is_transferencia("5151") is True
        assert cfop_is_transferencia("5102") is False

    def test_st(self):
        assert cfop_is_st("5405") is True
        assert cfop_is_st("5102") is False


# ═══════════════════════════════════════
#  CST PIS/COFINS
# ═══════════════════════════════════════


class TestCstPisCofins:
    def test_tabela_nao_vazia(self):
        assert len(CST_PIS_COFINS) >= 10

    def test_codigos_validos(self):
        for code in ["01", "02", "04", "49", "50", "70", "98", "99"]:
            assert is_valid_cst_pis_cofins(code), f"{code} deveria ser válido"

    def test_codigo_invalido(self):
        assert not is_valid_cst_pis_cofins("00")
        assert not is_valid_cst_pis_cofins("100")

    def test_descricao(self):
        assert get_cst_pis_cofins_descricao("01") is not None

    def test_saida(self):
        assert is_saida("01") is True
        assert is_saida("50") is False

    def test_entrada_com_credito(self):
        assert is_entrada_com_credito("50") is True
        assert is_entrada_com_credito("01") is False

    def test_entrada_sem_credito(self):
        assert is_entrada_sem_credito("70") is True
        assert is_entrada_sem_credito("50") is False


# ═══════════════════════════════════════
#  NCM
# ═══════════════════════════════════════


class TestNcm:
    def test_tabela_nao_vazia(self):
        assert len(NCM_VAREJO) > 100

    def test_formato_valido(self):
        assert is_valid_ncm_format("21069090") is True
        assert is_valid_ncm_format("2106.90.90") is True

    def test_formato_invalido(self):
        assert is_valid_ncm_format("123") is False
        assert is_valid_ncm_format("ABCDEFGH") is False

    def test_normalize(self):
        assert normalize_ncm("2106.90.90") == "21069090"

    def test_descricao(self):
        # Pega o primeiro NCM da tabela para testar
        first_ncm = next(iter(NCM_VAREJO))
        assert get_ncm_descricao(first_ncm) is not None

    def test_descricao_inexistente(self):
        assert get_ncm_descricao("00000000") is None

    def test_format_ncm(self):
        assert format_ncm("21069090") == "2106.90.90"

    def test_search(self):
        results = search_ncm("café")
        assert len(results) > 0
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)

    def test_search_vazio(self):
        assert search_ncm("") == []

    def test_ncms_eletricos_e_hidraulicos_relevantes_estao_na_base(self):
        assert get_ncm_descricao("73089010") is not None
        assert get_ncm_descricao("94054090") is not None


# ═══════════════════════════════════════
#  CEST
# ═══════════════════════════════════════


class TestCest:
    def test_tabela_nao_vazia(self):
        assert len(CEST_VAREJO) > 50

    def test_segmentos_tem_28(self):
        assert len(SEGMENTOS_CEST) == 28

    def test_formato_valido(self):
        assert is_valid_cest_format("0300700") is True
        assert is_valid_cest_format("03.007.00") is True

    def test_formato_invalido(self):
        assert is_valid_cest_format("123") is False
        assert is_valid_cest_format("ABCDEFG") is False

    def test_normalize(self):
        assert normalize_cest("03.007.00") == "0300700"

    def test_descricao(self):
        assert get_cest_descricao("0300700") is not None

    def test_descricao_inexistente(self):
        assert get_cest_descricao("9999999") is None

    def test_format(self):
        assert format_cest("0300700") == "03.007.00"

    def test_segmento(self):
        seg = get_segmento("0300700")
        assert seg is not None
        assert "bebidas" in seg.lower() or "Bebidas" in seg

    def test_search(self):
        results = search_cest("refrigerante")
        assert len(results) > 0

    def test_search_vazio(self):
        assert search_cest("") == []


# ═══════════════════════════════════════
#  Alíquotas UF
# ═══════════════════════════════════════


class TestAliquotasUf:
    def test_tabela_tem_27_ufs(self):
        assert len(ALIQUOTA_INTERNA) == 27

    def test_aliquota_sp(self):
        assert get_aliquota_interna("SP") == 18.0

    def test_aliquota_inexistente(self):
        assert get_aliquota_interna("XX") is None

    def test_interestadual_sul_sudeste(self):
        # SP → RJ = 12% (ambos Sul/Sudeste)
        assert get_aliquota_interestadual("SP", "RJ") == 12.0

    def test_interestadual_sul_para_norte(self):
        # SP (Sul/Sudeste) → AM (Norte) = 7%
        assert get_aliquota_interestadual("SP", "AM") == 7.0

    def test_interestadual_norte_para_sul(self):
        # AM (Norte) → SP (Sul/Sudeste) = 12%
        assert get_aliquota_interestadual("AM", "SP") == 12.0

    def test_interestadual_importado(self):
        assert get_aliquota_interestadual("SP", "RJ", importado=True) == 4.0

    def test_calcular_difal(self):
        resultado = calcular_difal(
            base_icms=1000.0,
            uf_origem="SP",
            uf_destino="BA",
        )
        assert resultado.aplicavel is True
        assert resultado.valor_difal > 0

    def test_difal_mesma_uf_nao_aplicavel(self):
        resultado = calcular_difal(
            base_icms=1000.0,
            uf_origem="SP",
            uf_destino="SP",
        )
        assert resultado.aplicavel is False
        assert resultado.valor_difal == 0.0


# ═══════════════════════════════════════
#  Cross Validator
# ═══════════════════════════════════════


class TestCrossValidator:
    """Testes do validador cruzado."""

    def test_nota_limpa_sem_findings(self):
        """Nota com dados válidos não gera findings."""
        nota = _make_nota([
            _make_item(cst="00", cfop="5102", ncm="21069090"),
        ])
        findings = validar_nota_cruzado(nota)
        # Pode ter 'info' de NCM desconhecido, mas sem erros
        erros = [f for f in findings if f.severidade == "erro"]
        assert len(erros) == 0

    def test_cst_invalido_gera_erro(self):
        nota = _make_nota([_make_item(cst="99")])
        findings = validar_nota_cruzado(nota)
        regras = {f.regra for f in findings if f.severidade == "erro"}
        assert "cst_icms_tabela" in regras

    def test_csosn_invalido_gera_erro(self):
        nota = _make_nota([_make_item(csosn="999")])
        findings = validar_nota_cruzado(nota)
        regras = {f.regra for f in findings if f.severidade == "erro"}
        assert "csosn_tabela" in regras

    def test_cfop_invalido_gera_erro(self):
        nota = _make_nota([_make_item(cfop="0000")])
        findings = validar_nota_cruzado(nota)
        regras = {f.regra for f in findings if f.severidade == "erro"}
        assert "cfop_tabela" in regras

    def test_ncm_formato_invalido_gera_erro(self):
        nota = _make_nota([_make_item(ncm="123")])
        findings = validar_nota_cruzado(nota)
        regras = {f.regra for f in findings if f.severidade == "erro"}
        assert "ncm_formato" in regras

    def test_ncm_desconhecido_gera_info(self):
        """NCM com formato válido mas fora da base de varejo → info."""
        nota = _make_nota([_make_item(ncm="99999999")])
        findings = validar_nota_cruzado(nota)
        regras = {f.regra for f in findings if f.severidade == "info"}
        assert "ncm_desconhecido_varejo" in regras

    def test_cst_csosn_coexistentes_gera_erro(self):
        nota = _make_nota([_make_item(cst="00", csosn="101")])
        findings = validar_nota_cruzado(nota)
        regras = {f.regra for f in findings if f.severidade == "erro"}
        assert "cst_csosn_coexistentes" in regras

    def test_cfop_st_sem_cst_st_gera_alerta(self):
        """CFOP de ST com CST não-ST gera alerta."""
        nota = _make_nota([_make_item(cfop="5405", cst="00")])
        findings = validar_nota_cruzado(nota)
        regras = {f.regra for f in findings if f.severidade == "alerta"}
        assert "cfop_st_cst_incompativel" in regras

    def test_cfop_st_com_cst_60_ok(self):
        """CFOP de ST com CST 60 não gera alerta de incompatibilidade."""
        nota = _make_nota([_make_item(cfop="5405", cst="60")])
        findings = validar_nota_cruzado(nota)
        regras = {f.regra for f in findings}
        assert "cfop_st_cst_incompativel" not in regras

    def test_valor_total_divergente_gera_alerta(self):
        nota = _make_nota([
            _make_item(
                quantidade=Decimal("2"),
                valor_unitario=Decimal("10.00"),
                valor_total_item=Decimal("25.00"),  # deveria ser 20.00
            ),
        ], valor_total_nota=Decimal("25.00"))
        findings = validar_nota_cruzado(nota)
        regras = {f.regra for f in findings if f.severidade == "alerta"}
        assert "valor_total_item_divergente" in regras

    def test_soma_itens_divergente_gera_alerta(self):
        itens = [
            _make_item(sequencia=1, valor_total_item=Decimal("10.00")),
            _make_item(sequencia=2, valor_total_item=Decimal("20.00")),
        ]
        nota = _make_nota(itens, valor_total_nota=Decimal("100.00"))
        findings = validar_nota_cruzado(nota)
        regras = {f.regra for f in findings if f.severidade == "alerta"}
        assert "soma_itens_divergente" in regras

    def test_nota_valida_sem_erros(self):
        """Nota completamente válida — sem erros nem alertas."""
        first_ncm = next(iter(NCM_VAREJO))
        itens = [
            _make_item(
                sequencia=1,
                cst="00",
                cfop="5102",
                ncm=first_ncm,
                quantidade=Decimal("2"),
                valor_unitario=Decimal("15.50"),
                valor_total_item=Decimal("31.00"),
            ),
        ]
        nota = _make_nota(itens)
        findings = validar_nota_cruzado(nota)
        erros = [f for f in findings if f.severidade == "erro"]
        alertas = [f for f in findings if f.severidade == "alerta"]
        assert len(erros) == 0
        assert len(alertas) == 0

    def test_findings_ordenados_por_severidade(self):
        """Erros vêm antes de alertas, que vêm antes de info."""
        nota = _make_nota([
            _make_item(
                cst="99",           # erro: cst_icms_tabela
                ncm="99999999",     # info: ncm_desconhecido_varejo
                quantidade=Decimal("2"),
                valor_unitario=Decimal("10.00"),
                valor_total_item=Decimal("25.00"),  # alerta: valor divergente
            ),
        ], valor_total_nota=Decimal("25.00"))
        findings = validar_nota_cruzado(nota)
        severidades = [f.severidade for f in findings]
        # Verificar que erros vêm antes de alertas, alertas antes de info
        last_erro = max((i for i, s in enumerate(severidades) if s == "erro"), default=-1)
        first_alerta = next((i for i, s in enumerate(severidades) if s == "alerta"), len(severidades))
        first_info = next((i for i, s in enumerate(severidades) if s == "info"), len(severidades))
        assert last_erro < first_alerta or last_erro == -1
        assert first_alerta <= first_info

    def test_campos_none_nao_geram_findings(self):
        """Item sem campos fiscais preenchidos não gera erro."""
        nota = _make_nota([_make_item()])
        findings = validar_nota_cruzado(nota)
        erros = [f for f in findings if f.severidade == "erro"]
        assert len(erros) == 0
