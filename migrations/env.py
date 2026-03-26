from logging.config import fileConfig
import os
import sys

from alembic import context
from sqlalchemy import create_engine, inspect, pool, text

# Adiciona o diretorio raiz ao path para encontrar o pacote 'app'
# O projeto esta estruturado como backend/app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

try:
    from app.core.config import settings
    from app.core.database import Base
    import app.models  # noqa: F401 - garante que os modelos sejam registrados no metadata
except ImportError as exc:
    print(f"Erro ao importar modulos: {exc}")
    print(f"PYTHONPATH: {sys.path}")
    raise

config = context.config

def _normalize_alembic_url(raw_url: str) -> str:
    if raw_url.startswith("postgresql+asyncpg://"):
        return raw_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if raw_url.startswith("sqlite+aiosqlite://"):
        return raw_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    return raw_url


if settings.DATABASE_URL:
    config.set_main_option("sqlalchemy.url", _normalize_alembic_url(settings.DATABASE_URL))

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
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def _ensure_version_table_capacity(connection) -> None:
    if connection.dialect.name != "postgresql":
        return

    inspector = inspect(connection)
    if not inspector.has_table("alembic_version"):
        connection.execute(
            text(
                "CREATE TABLE alembic_version ("
                "version_num VARCHAR(255) NOT NULL, "
                "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)"
                ")"
            )
        )
        connection.commit()
        return

    version_columns = {
        column["name"]: column for column in inspector.get_columns("alembic_version")
    }
    version_num = version_columns.get("version_num")
    current_length = getattr(version_num["type"], "length", None) if version_num else None
    if current_length is not None and current_length < 255:
        connection.execute(
            text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)")
        )
        connection.commit()


def run_migrations_online() -> None:
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _ensure_version_table_capacity(connection)
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
