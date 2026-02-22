import sqlite3
import shutil
import os

DB_PATH = r"C:\Users\usuario\loja-project-\backend\loja.db"
DB_RECOVER = r"C:\Users\usuario\loja-project-\backend\loja_recovered.db"

print("Tentando recuperar banco corrompido...")

try:
    # Conecta no banco corrompido e tenta exportar tudo
    conn_orig = sqlite3.connect(DB_PATH)
    conn_orig.execute("PRAGMA journal_mode=WAL")
    
    conn_new = sqlite3.connect(DB_RECOVER)
    
    # Copia estrutura e dados tabela por tabela
    tabelas_ok = []
    tabelas_erro = []
    
    cur = conn_orig.cursor()
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    tabelas = cur.fetchall()
    
    for nome, sql in tabelas:
        try:
            conn_new.execute(sql)
            rows = conn_orig.execute(f"SELECT * FROM [{nome}]").fetchall()
            if rows:
                placeholders = ",".join(["?" for _ in rows[0]])
                conn_new.executemany(f"INSERT INTO [{nome}] VALUES ({placeholders})", rows)
            conn_new.commit()
            tabelas_ok.append((nome, len(rows)))
            print(f"  ✓ {nome}: {len(rows)} registros")
        except Exception as e:
            tabelas_erro.append((nome, str(e)))
            print(f"  ✗ {nome}: {e}")
    
    conn_orig.close()
    conn_new.close()
    
    print(f"\nRecuperadas: {len(tabelas_ok)} tabelas")
    print(f"Com erro:    {len(tabelas_erro)} tabelas")
    
    # Verifica o banco recuperado
    conn_check = sqlite3.connect(DB_RECOVER)
    cur = conn_check.cursor()
    cur.execute("SELECT COUNT(*) FROM produto WHERE ativo=1")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ncm")
    ncms = cur.fetchone()[0]
    print(f"\nBanco recuperado: {total} produtos, {ncms} NCMs")
    conn_check.close()
    
    print(f"\nBanco recuperado salvo em: {DB_RECOVER}")
    print("Se OK, substitua manualmente o loja.db pelo loja_recovered.db")
    
except Exception as e:
    print(f"Erro geral: {e}")
