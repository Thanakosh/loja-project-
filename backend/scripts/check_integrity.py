import sqlite3

DB_PATH = r"C:\Users\usuario\loja-project-\backend\loja.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=== INTEGRIDADE DO BANCO ===\n")

# Verificação nativa do SQLite
cur.execute("PRAGMA integrity_check")
resultado = cur.fetchall()
for r in resultado[:10]:
    print(f"integrity_check: {r[0]}")

print()

# Contagem de cada tabela
tabelas = ['user','cliente','fornecedor','produto','venda','venda_item',
           'nota_fiscal','nota_fiscal_item','conta_receber','movimentacao_estoque',
           'transacao_estoque','orcamento','orcamento_item','ncm','refresh_token']

print("=== CONTAGEM POR TABELA ===")
for t in tabelas:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        count = cur.fetchone()[0]
        print(f"  {t:30s}: {count:>8} registros")
    except Exception as e:
        print(f"  {t:30s}: ERRO - {e}")

# Verificar integridade das foreign keys
print("\n=== CONSISTÊNCIA ===")

# Vendas sem cliente
cur.execute("SELECT COUNT(*) FROM venda WHERE cliente_id IS NOT NULL AND cliente_id NOT IN (SELECT id FROM cliente)")
print(f"  Vendas com cliente inexistente : {cur.fetchone()[0]}")

# Itens de venda sem produto
cur.execute("SELECT COUNT(*) FROM venda_item WHERE produto_id NOT IN (SELECT id FROM produto)")
orfaos = cur.fetchone()[0]
print(f"  Itens de venda sem produto     : {orfaos}")

# Itens de NF sem produto
cur.execute("SELECT COUNT(*) FROM nota_fiscal_item WHERE produto_id NOT IN (SELECT id FROM produto)")
print(f"  Itens de NF sem produto        : {cur.fetchone()[0]}")

if orfaos > 0:
    print(f"\n  → {orfaos} itens de venda referenciam produtos perdidos na corrupção")
    cur.execute("""
        SELECT vi.produto_id, COUNT(*) as vezes, SUM(vi.quantidade) as qtd_total
        FROM venda_item vi 
        WHERE vi.produto_id NOT IN (SELECT id FROM produto)
        GROUP BY vi.produto_id
        ORDER BY vezes DESC
        LIMIT 20
    """)
    print("  IDs de produtos perdidos (mais vendidos):")
    for r in cur.fetchall():
        print(f"    produto_id={r[0]}: {r[1]} vendas, {r[2]} unidades")

conn.close()
