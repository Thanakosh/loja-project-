import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Variáveis mínimas para inicialização dos módulos durante os testes
os.environ.setdefault("DATABASE_URL", "postgresql://user:password@localhost:5432/loja_db")
os.environ.setdefault("JWT_SECRET", "test-secret-key")
