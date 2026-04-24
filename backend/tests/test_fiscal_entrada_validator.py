from datetime import date
from decimal import Decimal

from app.fiscal.entrada_validator import validar_nota_entrada
from app.schemas.fiscal_payload import FiscalItemPayload, NotaFiscalPayloadNormalizado


def _item(**overrides) -> FiscalItemPayload:
    payload = {
        "sequencia": 1,
        "descricao": "Produto tributado",
        "quantidade": Decimal("2"),
        "unidade_comercial": "UN",
        "valor_unitario": Decimal("50"),
        "valor_total_item": Decimal("100"),
        "ncm": "22030000",
        "cfop": "6102",
        "cst": "00",
        "icms_base_calculo": Decimal("100"),
        "icms_aliquota": Decimal("12"),
        "icms_valor": Decimal("12"),
    }
    payload.update(overrides)
    return FiscalItemPayload.model_validate(payload)


def _nota(**overrides) -> NotaFiscalPayloadNormalizado:
    payload = {
        "versao_payload": "1.0.0",
        "fornecedor_nome": "Fornecedor Tributado LTDA",
        "fornecedor_cnpj": "12.345.678/0001-95",
        "fornecedor_uf": "GO",
        "numero_nota": "123",
        "data_emissao": date(2026, 4, 24),
        "valor_total_nota": Decimal("100"),
        "itens": [_item()],
    }
    payload.update(overrides)
    return NotaFiscalPayloadNormalizado.model_validate(payload)


def test_validacao_entrada_aprova_nota_sem_inconsistencias():
    resultado = validar_nota_entrada(_nota(), loja_uf="SP")

    assert resultado.status == "aprovada"
    assert resultado.score_risco == 0
    assert resultado.findings == []


def test_validacao_entrada_reprova_cnpj_invalido():
    resultado = validar_nota_entrada(_nota(fornecedor_cnpj="12.345.678/0001-23"), loja_uf="SP")

    assert resultado.status == "reprovada"
    assert any(finding.regra == "fornecedor_cnpj_invalido" for finding in resultado.findings)


def test_validacao_entrada_detecta_icms_divergente():
    nota = _nota(itens=[_item(icms_valor=Decimal("9.99"))])

    resultado = validar_nota_entrada(nota, loja_uf="SP")

    assert resultado.status == "reprovada"
    assert any(finding.regra == "icms_valor_divergente" for finding in resultado.findings)


def test_validacao_entrada_detecta_cfop_estadual_em_operacao_interestadual():
    nota = _nota(itens=[_item(cfop="5102")], fornecedor_uf="GO")

    resultado = validar_nota_entrada(nota, loja_uf="SP")

    assert resultado.status == "reprovada"
    assert any(finding.regra == "cfop_uf_incompativel" for finding in resultado.findings)


def test_validacao_entrada_alerta_codigo_icms_e_ncm_ausentes():
    nota = _nota(itens=[_item(ncm=None, cst=None, csosn=None)])

    resultado = validar_nota_entrada(nota, loja_uf="SP")

    assert resultado.status == "revisar"
    regras = {finding.regra for finding in resultado.findings}
    assert "ncm_ausente" in regras
    assert "codigo_icms_ausente" in regras


def test_validacao_entrada_simples_aceita_cst_de_fornecedor_regime_normal():
    resultado = validar_nota_entrada(
        _nota(),
        loja_uf="SP",
        regime_tributario="simples_nacional",
    )

    assert resultado.status == "aprovada"


def test_validacao_entrada_simples_alerta_cfop_st_sem_codigo_st():
    nota = _nota(
        fornecedor_uf="SP",
        itens=[_item(cfop="5405", cst=None, csosn="102")],
    )

    resultado = validar_nota_entrada(
        nota,
        loja_uf="SP",
        regime_tributario="simples_nacional",
    )

    assert resultado.status == "revisar"
    assert any(
        finding.regra == "simples_cfop_st_codigo_icms_incompativel"
        for finding in resultado.findings
    )


def test_validacao_entrada_simples_alerta_codigo_st_sem_cfop_st():
    nota = _nota(itens=[_item(cst="60")])

    resultado = validar_nota_entrada(
        nota,
        loja_uf="SP",
        regime_tributario="simples_nacional",
    )

    assert resultado.status == "revisar"
    assert any(
        finding.regra == "simples_codigo_icms_st_sem_cfop_st"
        for finding in resultado.findings
    )


def test_validacao_entrada_reprova_cst_e_csosn_no_mesmo_item():
    nota = _nota(itens=[_item(cst="00", csosn="102")])

    resultado = validar_nota_entrada(
        nota,
        loja_uf="SP",
        regime_tributario="simples_nacional",
    )

    assert resultado.status == "reprovada"
    assert any(finding.regra == "codigo_icms_duplicado" for finding in resultado.findings)
