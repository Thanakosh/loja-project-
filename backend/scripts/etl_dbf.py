"""
ETL: Migração DBF → SQLite
Importa dados históricos de 7 arquivos DBF do sistema legado para o banco SQLite do ERP Elétroluz.

Uso:
    cd backend
    python scripts/etl_dbf.py --source "C:\\Users\\usuario\\Downloads\\bkp-20260215T120344Z-1-001\\bkp"
    python scripts/etl_dbf.py --source "..." --phase 1      # Só clientes
    python scripts/etl_dbf.py --source "..." --dry-run       # Sem commit
"""

import argparse
import logging
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Garantir que o pacote 'app' é importável
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///loja.db")
os.environ.setdefault("JWT_SECRET", "etl-migration-temp-secret-key-32chars")

from dbfread import DBF
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models import (
    Cliente, ContaReceber, MovimentacaoEstoque,
    NotaFiscal, NotaFiscalItem, Produto, Venda, VendaItem,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("etl")

BATCH_SIZE = 1000


# ─────────────────────────── helpers ───────────────────────────

def safe_str(val: Any, max_len: int = 255) -> Optional[str]:
    """Converte para string, strip, ou None se vazio."""
    if val is None:
        return None
    s = str(val).strip()
    return s[:max_len] if s else None


def safe_float(val: Any) -> float:
    """Converte para float, 0 se None."""
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def safe_int(val: Any) -> int:
    """Converte para int, 0 se None."""
    if val is None:
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def safe_date(val: Any) -> Optional[date]:
    """Converte para date, None se inválido."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s or s == "None":
        return None
    # Tenta dd-mm-yyyy e dd/mm/yyyy
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def open_dbf(source_dir: str, filename: str) -> DBF:
    """Abre arquivo DBF com encoding latin-1 (padrão sistemas brasileiros)."""
    path = os.path.join(source_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    return DBF(path, encoding="latin-1", char_decode_errors="replace")


def safe_iter_dbf(dbf_table: DBF):
    """Itera registros de um DBF pulando registros corrompidos.

    dbfread raises ValueError during __next__() when it encounters
    corrupted date fields (e.g. null bytes). We catch those and skip.
    """
    errors = 0
    it = iter(dbf_table)
    while True:
        try:
            rec = next(it)
            yield rec
        except StopIteration:
            break
        except (ValueError, TypeError) as e:
            errors += 1
            if errors <= 5:
                log.warning(f"  Registro corrompido ignorado: {e}")
            elif errors == 6:
                log.warning("  ... suprimindo avisos adicionais de registros corrompidos")
    if errors:
        log.warning(f"  Total de registros corrompidos ignorados: {errors}")


def batch_commit(session: Session, objects: list, label: str, dry_run: bool = False) -> int:
    """Insere e faz commit em lote, retorna contagem."""
    if not objects:
        return 0
    session.add_all(objects)
    if not dry_run:
        session.commit()
    else:
        session.flush()
    count = len(objects)
    objects.clear()
    return count


# ─────────────────── PHASE 1: Clientes ────────────────────────

def phase1_clientes(session: Session, source_dir: str, dry_run: bool = False) -> Dict[int, int]:
    """
    Extrai clientes únicos de VENDA.DBF e enriquece com dados de NF01.DBF.
    Retorna dict: codigo_legado → cliente.id
    """
    log.info("═══ FASE 1: Extraindo clientes ═══")
    t0 = time.time()

    # Coletar clientes únicos de VENDA.DBF (tem mais dados de cliente)
    clientes: Dict[int, dict] = {}
    venda_dbf = open_dbf(source_dir, "VENDA.DBF")
    for rec in safe_iter_dbf(venda_dbf):
        cli = safe_int(rec.get("CLI"))
        if cli in clientes:
            continue
        clientes[cli] = {
            "codigo_legado": cli,
            "nome": safe_str(rec.get("CLINOME"), 60) or "SEM NOME",
            "cpf_cnpj": safe_str(rec.get("CLICPF"), 20),
            "endereco": safe_str(rec.get("CLIEND"), 80),
            "cidade": safe_str(rec.get("CLICID"), 30),
            "uf": safe_str(rec.get("CLIUF"), 2),
            "telefone": safe_str(rec.get("CLIFONE"), 20),
        }

    log.info(f"  VENDA.DBF: {len(clientes)} clientes únicos encontrados")

    # Enriquecer com NF01.DBF (tem CEP, endereço completo, CGC)
    nf01_dbf = open_dbf(source_dir, "NF01.DBF")
    enriched = 0
    for rec in safe_iter_dbf(nf01_dbf):
        cli = safe_int(rec.get("CLICOD"))
        if cli == 0 or cli not in clientes:
            # Criar cliente que só existe em NF01
            if cli != 0 and cli not in clientes:
                clientes[cli] = {
                    "codigo_legado": cli,
                    "nome": safe_str(rec.get("CLINOME"), 60) or "SEM NOME",
                    "cpf_cnpj": safe_str(rec.get("CLICGC"), 20),
                    "endereco": safe_str(rec.get("CLIEND"), 80),
                    "cidade": safe_str(rec.get("CLICID"), 30),
                    "uf": safe_str(rec.get("CLIUF"), 2),
                    "cep": safe_str(rec.get("CLICEP"), 10),
                    "telefone": safe_str(rec.get("CLIFONE"), 20),
                    "inscricao_estadual": safe_str(rec.get("CLIINSC"), 20),
                }
            continue
        c = clientes[cli]
        # Preencher campos vazios
        if not c.get("cpf_cnpj"):
            c["cpf_cnpj"] = safe_str(rec.get("CLICGC"), 20)
        if not c.get("cep"):
            c["cep"] = safe_str(rec.get("CLICEP"), 10)
        if not c.get("inscricao_estadual"):
            c["inscricao_estadual"] = safe_str(rec.get("CLIINSC"), 20)
        if not c.get("endereco") and safe_str(rec.get("CLIEND")):
            c["endereco"] = safe_str(rec.get("CLIEND"), 80)
        enriched += 1

    log.info(f"  NF01.DBF: {enriched} clientes enriquecidos")

    # Inserir no banco
    batch = []
    total = 0
    for data in clientes.values():
        batch.append(Cliente(**data))
        if len(batch) >= BATCH_SIZE:
            total += batch_commit(session, batch, "clientes", dry_run)
            log.info(f"  Clientes inseridos: {total}")
    total += batch_commit(session, batch, "clientes", dry_run)

    elapsed = time.time() - t0
    log.info(f"  ✓ Fase 1 concluída: {total} clientes em {elapsed:.1f}s")

    # Montar lookup codigo_legado → id
    lookup: Dict[int, int] = {}
    for row in session.execute(text("SELECT id, codigo_legado FROM cliente")):
        lookup[row[1]] = row[0]
    return lookup


# ─────────────────── PHASE 2: Produtos ────────────────────────

def phase2_produtos(session: Session, source_dir: str, dry_run: bool = False) -> Dict[int, int]:
    """
    Extrai produtos únicos de VENDAIT.DBF e NF02.DBF.
    Enriquece o Produto existente ou cria.
    Retorna dict: codigo_legado → produto.id
    """
    log.info("═══ FASE 2: Extraindo produtos ═══")
    t0 = time.time()

    # Lookup de produtos já existentes (se houver dados manuais)
    existing: Dict[str, int] = {}
    for row in session.execute(text("SELECT id, nome FROM produto")):
        existing[row[1].strip().upper()] = row[0]

    # Coletar produtos únicos de VENDAIT.DBF
    produtos: Dict[int, dict] = {}
    vendait_dbf = open_dbf(source_dir, "VENDAIT.DBF")
    for rec in safe_iter_dbf(vendait_dbf):
        cod = safe_int(rec.get("COD"))
        if cod in produtos:
            continue
        produtos[cod] = {
            "nome": safe_str(rec.get("NOME"), 255) or f"PRODUTO {cod}",
            "codigo_barras": safe_str(rec.get("CODBAR"), 13),
            "unidade": safe_str(rec.get("UN"), 2),
            "preco_unitario": safe_float(rec.get("UNIT")),
            "custo": safe_float(rec.get("CUSTO")),
            "marca": safe_str(rec.get("MARCA"), 15),
        }

    log.info(f"  VENDAIT.DBF: {len(produtos)} produtos únicos encontrados")

    # Enriquecer com NF02.DBF (tem NCM, CST, código barras)
    nf02_dbf = open_dbf(source_dir, "NF02.DBF")
    new_from_nf = 0
    for rec in safe_iter_dbf(nf02_dbf):
        cod = safe_int(rec.get("COD"))
        if cod in produtos:
            p = produtos[cod]
            if not p.get("ncm"):
                p["ncm"] = safe_str(rec.get("NCM"), 8)
            if not p.get("codigo_barras"):
                p["codigo_barras"] = safe_str(rec.get("CODBAR"), 13)
        else:
            produtos[cod] = {
                "nome": safe_str(rec.get("NOME"), 255) or f"PRODUTO {cod}",
                "codigo_barras": safe_str(rec.get("CODBAR"), 13),
                "unidade": safe_str(rec.get("UN"), 2),
                "preco_unitario": safe_float(rec.get("UNIT")),
                "custo": 0.0,
                "ncm": safe_str(rec.get("NCM"), 8),
            }
            new_from_nf += 1

    log.info(f"  NF02.DBF: {new_from_nf} produtos adicionais")

    # Inserir como Produto (usando o model existente)
    batch = []
    total = 0
    cod_to_id: Dict[int, int] = {}

    for cod, data in produtos.items():
        nome_upper = (data["nome"] or "").strip().upper()
        if nome_upper in existing:
            cod_to_id[cod] = existing[nome_upper]
            continue

        p = Produto(
            nome=data["nome"],
            descricao=f"Importado do sistema legado (COD={cod})",
            fornecedor="IMPORTADO_DBF",
            preco_unitario=data.get("preco_unitario", 0),
            preco_liquido=data.get("custo", 0) or data.get("preco_unitario", 0),
            codigo_ncm=data.get("ncm"),
            unidade=data.get("unidade"),
            ativo=True,
        )
        batch.append(p)
        if len(batch) >= BATCH_SIZE:
            total += batch_commit(session, batch, "produtos", dry_run)
            log.info(f"  Produtos inseridos: {total}")

    total += batch_commit(session, batch, "produtos", dry_run)

    elapsed = time.time() - t0
    log.info(f"  ✓ Fase 2 concluída: {total} produtos novos em {elapsed:.1f}s")

    # Rebuild lookup: todos os produtos (existentes + novos)
    for row in session.execute(text("SELECT id, nome FROM produto")):
        pass  # just warmup

    # Usar uma abordagem mais eficiente: mapear pelo COD original
    # Primeiro, mapeamos nome->id para todos os produtos no banco
    nome_to_id: Dict[str, int] = {}
    for row in session.execute(text("SELECT id, nome FROM produto")):
        nome_to_id[row[1].strip().upper()] = row[0]

    # Agora mapeamos cod->id via o nome do produto
    for cod, data in produtos.items():
        if cod not in cod_to_id:
            nome_upper = (data["nome"] or "").strip().upper()
            if nome_upper in nome_to_id:
                cod_to_id[cod] = nome_to_id[nome_upper]

    log.info(f"  Lookup: {len(cod_to_id)} produtos mapeados COD→ID")
    return cod_to_id


# ─────────────────── PHASE 3: Vendas ──────────────────────────

def phase3_vendas(session: Session, source_dir: str,
                  cliente_lookup: Dict[int, int],
                  produto_lookup: Dict[int, int],
                  dry_run: bool = False) -> Dict[int, int]:
    """
    Importa VENDA.DBF → Venda e VENDAIT.DBF → VendaItem.
    Retorna dict: (numero_legado, data_str) → venda.id
    """
    log.info("═══ FASE 3: Importando vendas ═══")
    t0 = time.time()

    # 3a: Cabeçalhos de venda
    venda_dbf = open_dbf(source_dir, "VENDA.DBF")
    batch = []
    total = 0
    # Track (NUM, DAT_str) → row index for dedup, then map to id after insert
    seen_vendas: set = set()
    venda_keys: list = []  # list of (num, dat_str) in insert order
    for rec in safe_iter_dbf(venda_dbf):
        num = safe_int(rec.get("NUM"))
        dat = safe_date(rec.get("DAT")) or date(2016, 1, 1)
        dat_str = str(dat)
        key = (num, dat_str)
        if key in seen_vendas:
            continue  # skip true duplicate (same NUM + same DAT)
        seen_vendas.add(key)
        cli = safe_int(rec.get("CLI"))
        v = Venda(
            numero_legado=num,
            data=dat,
            hora=safe_str(rec.get("HORA"), 5),
            cliente_id=cliente_lookup.get(cli),
            vendedor=safe_str(rec.get("VEND"), 10),
            total=safe_float(rec.get("TOTAL")),
            desconto=safe_float(rec.get("DESCTO")),
            forma_pagamento=safe_int(rec.get("FPG")),
            fatura=safe_str(rec.get("FATURA"), 10),
            situacao=safe_int(rec.get("SIT")),
            cancelada=safe_int(rec.get("CANCELA")) == 1,
            cupom=safe_int(rec.get("CUPOM")),
            observacao=safe_str(
                ((safe_str(rec.get("OBS1"), 60) or "") + " " +
                 (safe_str(rec.get("OBS2"), 60) or "")).strip(),
                120
            ),
            entrega=safe_str(rec.get("ENTREGA"), 80),
            entrega_data=safe_date(rec.get("ENTREGADT")),
        )
        batch.append(v)
        venda_keys.append(key)
        if len(batch) >= BATCH_SIZE:
            total += batch_commit(session, batch, "vendas", dry_run)
            if total % 10000 == 0:
                log.info(f"  Vendas inseridas: {total}")

    total += batch_commit(session, batch, "vendas", dry_run)
    log.info(f"  VENDA.DBF: {total} vendas inseridas (dedup de {len(seen_vendas)})")

    # Lookup (numero_legado, data) → venda.id
    venda_lookup: Dict[tuple, int] = {}
    for row in session.execute(text("SELECT id, numero_legado, data FROM venda")):
        venda_lookup[(row[1], str(row[2]))] = row[0]

    # 3b: Itens de venda
    vendait_dbf = open_dbf(source_dir, "VENDAIT.DBF")
    batch = []
    total_itens = 0
    for rec in safe_iter_dbf(vendait_dbf):
        num = safe_int(rec.get("NUM"))
        dat = safe_date(rec.get("DAT"))
        dat_str = str(dat) if dat else ""
        venda_id = venda_lookup.get((num, dat_str))
        if venda_id is None:
            continue
        cod = safe_int(rec.get("COD"))
        item = VendaItem(
            venda_id=venda_id,
            produto_id=produto_lookup.get(cod),
            codigo_legado=cod,
            nome_produto=safe_str(rec.get("NOME"), 50),
            codigo_barras=safe_str(rec.get("CODBAR"), 13),
            unidade=safe_str(rec.get("UN"), 2),
            quantidade=safe_float(rec.get("QTD")),
            preco_unitario=safe_float(rec.get("UNIT")),
            preco_total=safe_float(rec.get("TOTAL")),
            custo=safe_float(rec.get("CUSTO")),
            desconto=safe_float(rec.get("DESCTO")),
            marca=safe_str(rec.get("MARCA"), 15),
            grupo=safe_int(rec.get("GRUPO")),
        )
        batch.append(item)
        if len(batch) >= BATCH_SIZE:
            total_itens += batch_commit(session, batch, "venda_itens", dry_run)
            if total_itens % 50000 == 0:
                log.info(f"  Itens de venda inseridos: {total_itens}")

    total_itens += batch_commit(session, batch, "venda_itens", dry_run)

    elapsed = time.time() - t0
    log.info(f"  ✓ Fase 3 concluída: {total} vendas + {total_itens} itens em {elapsed:.1f}s")
    return venda_lookup


# ──────────────── PHASE 4: Contas a Receber ───────────────────

def phase4_contas_receber(session: Session, source_dir: str,
                          cliente_lookup: Dict[int, int],
                          dry_run: bool = False):
    """Importa CR.DBF → ContaReceber."""
    log.info("═══ FASE 4: Importando contas a receber ═══")
    t0 = time.time()

    cr_dbf = open_dbf(source_dir, "CR.DBF")
    batch = []
    total = 0
    for rec in safe_iter_dbf(cr_dbf):
        cli = safe_int(rec.get("CLI"))
        cr = ContaReceber(
            cliente_id=cliente_lookup.get(cli),
            documento=safe_int(rec.get("DOC")),
            parcela=safe_int(rec.get("PAR")),
            vendedor=safe_str(rec.get("VEND"), 15),
            fatura=safe_str(rec.get("FATURA"), 10),
            data_emissao=safe_date(rec.get("EMI")),
            data_vencimento=safe_date(rec.get("VEN")),
            data_pagamento=safe_date(rec.get("PAG")),
            valor=safe_float(rec.get("VALOR")),
            desconto=safe_float(rec.get("DESCTO")),
            juros=safe_float(rec.get("JUROS")),
            valor_pago=safe_float(rec.get("PAGO")),
            historico=safe_str(rec.get("HIS"), 40),
            cheque=safe_str(rec.get("CHEQUE"), 10),
            cobranca=safe_str(rec.get("COB"), 15),
        )
        batch.append(cr)
        if len(batch) >= BATCH_SIZE:
            total += batch_commit(session, batch, "contas_receber", dry_run)
            if total % 10000 == 0:
                log.info(f"  Contas inseridas: {total}")

    total += batch_commit(session, batch, "contas_receber", dry_run)

    elapsed = time.time() - t0
    log.info(f"  ✓ Fase 4 concluída: {total} contas a receber em {elapsed:.1f}s")


# ──────────────── PHASE 5: Movimentação ───────────────────────

def phase5_movimentacao(session: Session, source_dir: str,
                        produto_lookup: Dict[int, int],
                        dry_run: bool = False):
    """Importa MOVPROD2.DBF → MovimentacaoEstoque."""
    log.info("═══ FASE 5: Importando movimentações de estoque ═══")
    t0 = time.time()

    mov_dbf = open_dbf(source_dir, "MOVPROD2.DBF")
    batch = []
    total = 0
    for rec in safe_iter_dbf(mov_dbf):
        cod = safe_int(rec.get("COD"))
        m = MovimentacaoEstoque(
            data=safe_date(rec.get("DAT")) or date(2016, 1, 1),
            hora=safe_str(rec.get("HORA"), 5),
            operador=safe_str(rec.get("POR"), 10),
            produto_id=produto_lookup.get(cod),
            codigo_legado=cod,
            nome_produto=safe_str(rec.get("NOME"), 50),
            unidade=safe_str(rec.get("UN"), 2),
            saldo_anterior=safe_float(rec.get("ANTES")),
            entrada=safe_float(rec.get("ENTRADA")),
            saida=safe_float(rec.get("SAIDA")),
            saldo_final=safe_float(rec.get("SALDO")),
            documento=safe_int(rec.get("DOC")),
            historico=safe_str(rec.get("HIST"), 50),
        )
        batch.append(m)
        if len(batch) >= BATCH_SIZE:
            total += batch_commit(session, batch, "movimentacoes", dry_run)
            if total % 50000 == 0:
                log.info(f"  Movimentações inseridas: {total}")

    total += batch_commit(session, batch, "movimentacoes", dry_run)

    elapsed = time.time() - t0
    log.info(f"  ✓ Fase 5 concluída: {total} movimentações em {elapsed:.1f}s")


# ──────────────── PHASE 6: Notas Fiscais ──────────────────────

def phase6_notas_fiscais(session: Session, source_dir: str,
                         cliente_lookup: Dict[int, int],
                         produto_lookup: Dict[int, int],
                         dry_run: bool = False):
    """Importa NF01.DBF → NotaFiscal, NF02.DBF → NotaFiscalItem."""
    log.info("═══ FASE 6: Importando notas fiscais ═══")
    t0 = time.time()

    # 6a: Cabeçalhos NF-e
    nf01_dbf = open_dbf(source_dir, "NF01.DBF")
    batch = []
    total = 0
    for rec in safe_iter_dbf(nf01_dbf):
        num = safe_int(rec.get("NUM"))
        cli = safe_int(rec.get("CLICOD"))
        nf = NotaFiscal(
            numero_legado=num,
            chave_acesso=safe_str(rec.get("CHAVE"), 44),
            serie=safe_str(rec.get("SERIE"), 3),
            data_emissao=safe_date(rec.get("DAT")),
            hora_emissao=safe_str(rec.get("HORAEMI"), 8),
            data_saida=safe_date(rec.get("SAIDA")),
            hora_saida=safe_str(rec.get("HORASAI"), 8),
            situacao=safe_int(rec.get("SIT")),
            entrada_saida=safe_str(rec.get("ES"), 1),
            cfop=safe_str(rec.get("CFOP"), 5),
            cfop_descricao=safe_str(rec.get("CFOPD"), 50),
            cliente_id=cliente_lookup.get(cli),
            protocolo=safe_str(rec.get("PROTOCOLO"), 15),
            data_protocolo=safe_str(rec.get("DHPROT"), 20),
            protocolo_cancelamento=safe_str(rec.get("PROTCAN"), 20),
            data_cancelamento=safe_date(rec.get("DTCAN")),
            valor_produtos=safe_float(rec.get("VLRPROD")),
            valor_total=safe_float(rec.get("VLRTOTAL")),
            valor_desconto=safe_float(rec.get("VLRDESC")),
            valor_frete=safe_float(rec.get("VLRFRETE")),
            valor_icms=safe_float(rec.get("VLRICM")),
            base_icms=safe_float(rec.get("BASEICM")),
            base_substituicao=safe_float(rec.get("BASESUB")),
            valor_substituicao=safe_float(rec.get("VLRSUB")),
            valor_ipi=safe_float(rec.get("VLRIPI")),
            valor_seguro=safe_float(rec.get("VLRSEGURO")),
            valor_outras=safe_float(rec.get("VLROUTRA")),
            observacao=safe_str(rec.get("OBS"), 80),
        )
        batch.append(nf)
        if len(batch) >= BATCH_SIZE:
            total += batch_commit(session, batch, "notas_fiscais", dry_run)
            if total % 10000 == 0:
                log.info(f"  NF-e inseridas: {total}")

    total += batch_commit(session, batch, "notas_fiscais", dry_run)
    log.info(f"  NF01.DBF: {total} notas fiscais inseridas")

    # Lookup (numero_legado, data_emissao) → nota_fiscal.id
    nf_lookup: Dict[tuple, int] = {}
    for row in session.execute(text("SELECT id, numero_legado, data_emissao FROM nota_fiscal")):
        nf_lookup[(row[1], str(row[2]))] = row[0]

    # 6b: Itens NF-e
    nf02_dbf = open_dbf(source_dir, "NF02.DBF")
    batch = []
    total_itens = 0
    for rec in safe_iter_dbf(nf02_dbf):
        num = safe_int(rec.get("NUM"))
        dat = safe_date(rec.get("DAT"))
        dat_str = str(dat) if dat else ""
        nf_id = nf_lookup.get((num, dat_str))
        if nf_id is None:
            continue
        cod = safe_int(rec.get("COD"))
        item = NotaFiscalItem(
            nota_fiscal_id=nf_id,
            produto_id=produto_lookup.get(cod),
            codigo_legado=cod,
            nome_produto=safe_str(rec.get("NOME"), 50),
            unidade=safe_str(rec.get("UN"), 2),
            quantidade=safe_float(rec.get("QTD")),
            preco_unitario=safe_float(rec.get("UNIT")),
            preco_total=safe_float(rec.get("TOTAL")),
            icms=safe_float(rec.get("ICM")),
            ipi=safe_float(rec.get("IPI")),
            cfop=safe_str(rec.get("CFOP"), 5),
            cst=safe_str(rec.get("CST"), 3),
            ncm=safe_str(rec.get("NCM"), 8),
            codigo_barras=safe_str(rec.get("CODBAR"), 13),
            pis=safe_float(rec.get("PIS")),
            cofins=safe_float(rec.get("COFINS")),
            cest=safe_str(rec.get("CEST"), 7),
            pedido=safe_str(rec.get("PEDIDO"), 10),
        )
        batch.append(item)
        if len(batch) >= BATCH_SIZE:
            total_itens += batch_commit(session, batch, "nf_itens", dry_run)
            if total_itens % 20000 == 0:
                log.info(f"  Itens NF-e inseridos: {total_itens}")

    total_itens += batch_commit(session, batch, "nf_itens", dry_run)

    elapsed = time.time() - t0
    log.info(f"  ✓ Fase 6 concluída: {total} NFs + {total_itens} itens em {elapsed:.1f}s")


# ──────────────────── Report & Main ───────────────────────────

def report(session: Session):
    """Exibe contagem final de todas as tabelas."""
    log.info("")
    log.info("═══ RELATÓRIO FINAL ═══")
    tables = [
        "cliente", "produto", "venda", "venda_item",
        "conta_receber", "movimentacao_estoque",
        "nota_fiscal", "nota_fiscal_item",
    ]
    for t in tables:
        try:
            count = session.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            log.info(f"  {t:30s} {count:>10,}")
        except Exception:
            log.info(f"  {t:30s} {'N/A':>10}")


def main():
    parser = argparse.ArgumentParser(description="ETL: DBF → SQLite")
    parser.add_argument("--source", required=True, help="Diretório com os arquivos .DBF")
    parser.add_argument("--db", default=None, help="URL do banco (default: DATABASE_URL do .env)")
    parser.add_argument("--phase", type=int, default=0, help="Executar apenas uma fase (1-6), 0=todas")
    parser.add_argument("--batch-size", type=int, default=1000, help="Tamanho do lote (default: 1000)")
    parser.add_argument("--dry-run", action="store_true", help="Não faz commit (flush only)")
    args = parser.parse_args()

    global BATCH_SIZE
    BATCH_SIZE = args.batch_size

    # Setup banco
    db_url = args.db or os.environ.get("DATABASE_URL", "sqlite:///loja.db")
    log.info(f"Banco: {db_url}")
    log.info(f"Fonte: {args.source}")
    log.info(f"Batch: {BATCH_SIZE}")
    if args.dry_run:
        log.info("⚠ DRY RUN — nenhum dado será persistido")

    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
        echo=False,
    )

    # Otimizações SQLite
    if "sqlite" in db_url:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.execute(text("PRAGMA cache_size=-64000"))  # 64MB
            conn.commit()

    # Criar tabelas (se não existirem)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()

    t_total = time.time()

    try:
        run_phase = args.phase

        # Fases 1 e 2 sempre rodam pois geram lookups necessários
        if run_phase in (0, 1, 2, 3, 4, 5, 6):
            cliente_lookup = phase1_clientes(session, args.source, args.dry_run)
        else:
            cliente_lookup = {}

        if run_phase in (0, 2, 3, 5, 6):
            produto_lookup = phase2_produtos(session, args.source, args.dry_run)
        else:
            produto_lookup = {}

        if run_phase in (0, 3):
            phase3_vendas(session, args.source, cliente_lookup, produto_lookup, args.dry_run)

        if run_phase in (0, 4):
            phase4_contas_receber(session, args.source, cliente_lookup, args.dry_run)

        if run_phase in (0, 5):
            phase5_movimentacao(session, args.source, produto_lookup, args.dry_run)

        if run_phase in (0, 6):
            phase6_notas_fiscais(session, args.source, cliente_lookup, produto_lookup, args.dry_run)

        if args.dry_run:
            session.rollback()
            log.info("DRY RUN concluído — rollback executado")
        else:
            report(session)

    except Exception:
        session.rollback()
        log.exception("Erro durante ETL")
        raise
    finally:
        session.close()

    elapsed = time.time() - t_total
    log.info(f"\n✓ ETL finalizado em {elapsed:.1f}s ({elapsed/60:.1f} min)")


if __name__ == "__main__":
    main()
