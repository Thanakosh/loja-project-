"""
Entry point para o backend empacotado com PyInstaller.
Inicia o uvicorn servindo a API FastAPI na porta 8000.
"""
import os
import sys

# Garantir que o diretório do executável seja o working directory
if getattr(sys, 'frozen', False):
    # Executando como .exe empacotado
    base_dir = os.path.dirname(sys.executable)
    os.chdir(base_dir)
    # Adicionar o diretório ao PATH para encontrar dependências
    sys.path.insert(0, base_dir)

# Configurar variáveis de ambiente (loja.db como banco principal)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.join(os.getcwd(), 'loja.db')}")
os.environ.setdefault("JWT_SECRET", "demo-secret-key-apenas-para-demonstracao-2026")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("CORS_ORIGINS", '["*"]')
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("LOG_FORMAT", "text")

import uvicorn
from app.main import app as application  # import direto para PyInstaller encontrar

def main():
    print("=" * 50)
    print("  Loja API - Servidor de Demonstração")
    print("  http://localhost:8000")
    print("  Docs: http://localhost:8000/docs")
    print("=" * 50)
    print()
    uvicorn.run(
        application,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )

if __name__ == "__main__":
    main()
