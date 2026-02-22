import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "loja.db")
DB_PATH = os.path.normpath(DB_PATH)
print(f"Banco: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tabelas = [r[0] for r in cur.fetchall()]
print(f"Tabelas: {tabelas}")
conn.close()
