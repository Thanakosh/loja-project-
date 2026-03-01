"""Carga inicial de estoque a partir do legado `movimentacao_estoque`.

Uso:
    python scripts/carga_estoque_inicial.py
    python scripts/carga_estoque_inicial.py --dry-run
    python scripts/carga_estoque_inicial.py --limite 100
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from sqlalchemy import create_engine, desc, func, select
from sqlalchemy.orm import Session

# Evita erro de configuração ao importar modelos fora do contexto da API
DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "loja.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
os.environ.setdefault("JWT_SECRET", "script-carga-estoque-inicial")

# Garante imports de `app.*` quando executado via `python scripts/...`
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.models.movimentacao_estoque import MovimentacaoEstoque  # noqa: E402
from app.models.produto import Produto  # noqa: E402
from app.models.transacao_estoque import TipoTransacao, TransacaoEstoque  # noqa: E402

MOTIVO_SALDO_INICIAL = "Saldo inicial importado do sistema legado"


def _latest_legacy_balance_subquery() -> object:
    """Subquery com o último saldo legado por produto (data DESC, id DESC)."""
    ranking = (
        select(
            MovimentacaoEstoque.produto_id.label("produto_id"),
            MovimentacaoEstoque.saldo_final.label("saldo_final"),
            func.row_number()
            .over(
                partition_by=MovimentacaoEstoque.produto_id,
                order_by=(desc(MovimentacaoEstoque.data), desc(MovimentacaoEstoque.id)),
            )
            .label("row_num"),
        )
        .where(MovimentacaoEstoque.produto_id.is_not(None))
        .subquery()
    )

    return (
        select(
            ranking.c.produto_id,
            ranking.c.saldo_final,
        )
        .where(ranking.c.row_num == 1)
        .subquery()
    )


def executar_carga(session: Session, limite: int | None = None, dry_run: bool = False) -> None:
    latest_balance_sq = _latest_legacy_balance_subquery()

    existing_initial_ids = set(
        session.scalars(
            select(TransacaoEstoque.produto_id).where(
                TransacaoEstoque.motivo == MOTIVO_SALDO_INICIAL
            )
        ).all()
    )

    produtos_stmt = select(Produto.id).order_by(Produto.id)
    if limite is not None:
        produtos_stmt = produtos_stmt.limit(limite)

    produto_ids = session.scalars(produtos_stmt).all()
    if not produto_ids:
        print("Nenhum produto encontrado para processar.")
        return

    balances = dict(
        session.execute(
            select(latest_balance_sq.c.produto_id, latest_balance_sq.c.saldo_final).where(
                latest_balance_sq.c.produto_id.in_(produto_ids)
            )
        ).all()
    )

    produtos_carregados = 0
    produtos_sem_historico = 0
    produtos_saldo_nao_positivo = 0
    produtos_ja_carregados = 0
    total_unidades = 0

    for produto_id in produto_ids:
        if produto_id in existing_initial_ids:
            produtos_ja_carregados += 1
            continue

        saldo_final = balances.get(produto_id)
        if saldo_final is None:
            produtos_sem_historico += 1
            continue

        quantidade = int(saldo_final)
        if quantidade <= 0:
            produtos_saldo_nao_positivo += 1
            continue

        session.add(
            TransacaoEstoque(
                produto_id=produto_id,
                tipo=TipoTransacao.ENTRADA,
                quantidade=quantidade,
                motivo=MOTIVO_SALDO_INICIAL,
                usuario_id=None,
            )
        )

        produtos_carregados += 1
        total_unidades += quantidade

    session.flush()

    if dry_run:
        session.rollback()
        print("[DRY-RUN] Transação revertida após flush (nenhum dado persistido).")
    else:
        session.commit()

    print("\n=== RESUMO DA CARGA INICIAL DE ESTOQUE ===")
    print(f"Produtos carregados (saldo > 0): {produtos_carregados}")
    print(f"Produtos ignorados (sem histórico legado): {produtos_sem_historico}")
    print(f"Total de unidades inseridas: {total_unidades}")
    print(f"Produtos pulados (já carregados): {produtos_ja_carregados}")
    print(f"Produtos ignorados (saldo <= 0): {produtos_saldo_nao_positivo}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Carga de saldo inicial para transacao_estoque")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa a carga sem persistir (faz flush e rollback ao final).",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        help="Processa apenas os primeiros N produtos (ordenados por id).",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="URL do banco SQLAlchemy. Padrão: sqlite:///backend/loja.db",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    database_url = args.database_url or os.environ["DATABASE_URL"]
    engine = create_engine(database_url)

    with Session(bind=engine) as session:
        executar_carga(session=session, limite=args.limite, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
