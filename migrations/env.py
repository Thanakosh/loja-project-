from logging.config import fileConfig
import os
import sys
from alembic import context
from sqlalchemy import pool # Adicionado para run_migrations_online do template original

# Adiciona o diretório /code ao path para encontrar 'backend'
sys.path.insert(0, '/code')

# Importa Base e engine de backend.app.core.database
# e os modelos que o Alembic precisa conhecer
from backend.app.core.database import Base, engine, settings # settings também é útil aqui
from backend.app.models import estoque # Certifique-se que este model existe e Base está nele

config = context.config

# Use a URL do banco de dados das configurações do projeto
# Isso substitui a necessidade de sqlalchemy.url no alembic.ini
if settings.database_url:
    config.set_main_option('sqlalchemy.url', settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # usa o engine importado do projeto
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            poolclass=pool.NullPool, # Adicionado do template original
            compare_type=True, # Adicionado para melhor detecção de tipos
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
