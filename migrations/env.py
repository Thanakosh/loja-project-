from logging.config import fileConfig
import os
import sys
from alembic import context
from sqlalchemy import pool

# Adiciona o diretório raiz ao path para encontrar o pacote 'app'
# O projeto está estruturado como backend/app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

# Importa Base e engine de app.core.database
try:
    from app.core.database import Base, engine
    from app.core.config import settings
    # Importar todos os modelos para que o Alembic os reconheça
    from app.models import User, Produto, Estoque, Orcamento, TransacaoEstoque
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print(f"PYTHONPATH: {sys.path}")
    raise

config = context.config

# Use a URL do banco de dados das configurações do projeto
if settings.DATABASE_URL:
    config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    # No SQLite, não podemos usar pool.NullPool com a mesma facilidade em alguns casos,
    # mas o engine já está configurado no app.core.database
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
