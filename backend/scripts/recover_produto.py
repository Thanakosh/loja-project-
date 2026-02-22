"""
Tenta recuperar a tabela produto linha por linha,
pulando as linhas corrompidas.
"""
import sqlite3

DB_PATH = r"C:\Users\usuario\loja-project-\backend\loja.db"
DB_RECOVER = r"C:\Users\usuario\loja-project-\backend\loja_recovered.db"

conn_orig = sqlite3.connect(DB_PATH)
conn_orig.row_factory = sqlite3.Row
conn_new = sqlite3.connect(DB_RECOVER)

# Pegar estrutura da tabela produto
cur_orig = conn_orig.cursor()
cur_orig.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='produto'")
sql_criar = cur_orig.fetchone()[0]

# Criar tabela produto no banco recuperado
try:
    conn_new.execute(sql_criar)
    conn_new.commit()
    print("Tabela produto criada no banco recuperado")
except Exception as e:
    print(f"Tabela ja existe ou erro: {e}")

# Descobrir numero maximo de rowid
try:
    max_rowid = conn_orig.execute("SELECT MAX(rowid) FROM produto").fetchone()[0]
    print(f"Max rowid: {max_rowid}")
except:
    max_rowid = 15000  # chute conservador

# Recuperar linha por linha
ok = 0
erro = 0
cur_new = conn_new.cursor()

for rowid in range(1, (max_rowid or 15000) + 1):
    try:
        row = conn_orig.execute(f"SELECT * FROM produto WHERE rowid={rowid}").fetchone()
        if row:
            placeholders = ",".join(["?" for _ in row])
            cur_new.execute(f"INSERT OR IGNORE INTO produto VALUES ({placeholders})", tuple(row))
            ok += 1
    except Exception:
        erro += 1

conn_new.commit()

total = conn_new.execute("SELECT COUNT(*) FROM produto").fetchone()[0]
com_ncm = conn_new.execute("SELECT COUNT(*) FROM produto WHERE codigo_ncm IS NOT NULL AND codigo_ncm != '' AND length(codigo_ncm)=8").fetchone()[0]

print(f"\nResultado:")
print(f"  Linhas recuperadas : {ok}")
print(f"  Linhas corrompidas : {erro}")
print(f"  Total no banco     : {total}")
print(f"  Com NCM            : {com_ncm}")

conn_orig.close()
conn_new.close()

print("\nPronto! Banco em: loja_recovered.db")
