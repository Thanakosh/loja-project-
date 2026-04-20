import json
import logging
import os
import secrets
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

from alembic import command
from alembic.config import Config
from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

import app.models  # noqa: F401 - garante metadata completo para fallback/create_all
from app.core.database import Base, get_async_engine
from app.core.security import get_password_hash
from app.models.user import User

logger = logging.getLogger(__name__)

FIRST_RUN_FILENAME = "desktop-first-run.json"
DEFAULT_DESKTOP_ADMIN_EMAIL = "admin@loja-project.app"


@dataclass(slots=True)
class DesktopInitialAdmin:
    email: str
    password: str
    full_name: str
    generated_at: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def is_desktop_mode() -> bool:
    return os.environ.get("LOJA_DESKTOP_MODE", "").strip() == "1"


def get_runtime_base_dir() -> Path:
    runtime_base_dir = os.environ.get("LOJA_RUNTIME_BASE_DIR")
    return Path(runtime_base_dir) if runtime_base_dir else Path.cwd()


def get_runtime_resource_dir() -> Path:
    configured_resource_dir = os.environ.get("LOJA_RESOURCE_BASE_DIR")
    if configured_resource_dir:
        return Path(configured_resource_dir)

    runtime_base_dir = get_runtime_base_dir()
    internal_dir = runtime_base_dir / "_internal"
    if internal_dir.exists():
        return internal_dir

    meipass_dir = getattr(sys, "_MEIPASS", None)
    if meipass_dir:
        return Path(meipass_dir)

    return runtime_base_dir


def get_desktop_data_dir() -> Path:
    data_dir = os.environ.get("LOJA_APP_DATA_DIR")
    if data_dir:
        return Path(data_dir)
    return get_runtime_base_dir() / "data"


def get_first_run_file_path() -> Path:
    return get_desktop_data_dir() / FIRST_RUN_FILENAME


def load_initial_admin_info() -> dict[str, str] | None:
    info_path = get_first_run_file_path()
    if not info_path.exists():
        return None

    try:
        payload = json.loads(info_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Nao foi possivel ler o arquivo de bootstrap desktop: %s", exc)
        return None

    if not isinstance(payload, dict):
        logger.warning("Arquivo de bootstrap desktop invalido: formato inesperado")
        return None

    return {
        "email": str(payload.get("email", "")),
        "password": str(payload.get("password", "")),
        "full_name": str(payload.get("full_name", "")),
        "generated_at": str(payload.get("generated_at", "")),
    }


def _get_sqlite_database_path() -> Path | None:
    database_url = (os.environ.get("DATABASE_URL") or "").strip()
    if not database_url.startswith("sqlite:///"):
        return None

    raw_path = database_url.removeprefix("sqlite:///")
    return Path(unquote(raw_path))


def _run_alembic_migrations() -> None:
    alembic_config = _build_alembic_config()
    command.upgrade(alembic_config, "head")


def _build_alembic_config() -> Config:
    resource_base_dir = get_runtime_resource_dir()
    alembic_ini = resource_base_dir / "alembic.ini"
    migrations_dir = resource_base_dir / "migrations"

    if not alembic_ini.exists():
        raise FileNotFoundError(f"alembic.ini nao encontrado em {alembic_ini}")
    if not migrations_dir.exists():
        raise FileNotFoundError(f"Diretorio de migrations nao encontrado em {migrations_dir}")

    alembic_config = Config(str(alembic_ini))
    alembic_config.set_main_option("script_location", str(migrations_dir))
    return alembic_config


def _stamp_alembic_head() -> None:
    alembic_config = _build_alembic_config()
    command.stamp(alembic_config, "head")


async def _fallback_create_schema() -> None:
    engine = get_async_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


def _sqlite_schema_needs_alembic_stamp() -> bool:
    sqlite_db_path = _get_sqlite_database_path()
    if sqlite_db_path is None or not sqlite_db_path.exists():
        return False

    with sqlite3.connect(sqlite_db_path) as connection:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()
        version_rows = []
        if any(str(row[0]) == "alembic_version" for row in rows):
            try:
                version_rows = connection.execute("SELECT version_num FROM alembic_version").fetchall()
            except sqlite3.DatabaseError:
                version_rows = []

    table_names = {str(row[0]) for row in rows}
    user_tables = table_names - {"alembic_version"}
    if not user_tables:
        return False

    if "alembic_version" not in table_names:
        return True

    return len(version_rows) == 0


def _resolve_admin_email() -> str:
    raw_email = (os.environ.get("LOJA_INITIAL_ADMIN_EMAIL") or "").strip()
    return raw_email or DEFAULT_DESKTOP_ADMIN_EMAIL


def _resolve_admin_full_name() -> str:
    raw_name = (os.environ.get("LOJA_INITIAL_ADMIN_NAME") or "").strip()
    return raw_name or "Administrador"


def _resolve_admin_password() -> str:
    raw_password = (os.environ.get("LOJA_INITIAL_ADMIN_PASSWORD") or "").strip()
    return raw_password or secrets.token_urlsafe(12)


def _is_valid_user_email(email: str) -> bool:
    if not email:
        return False

    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


async def _repair_desktop_admin_identity() -> dict[str, str] | None:
    desired_email = _resolve_admin_email()
    existing_hint = load_initial_admin_info()
    engine = get_async_engine()
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as db:
        users = (await db.execute(select(User).order_by(User.id))).scalars().all()
        if len(users) != 1:
            return existing_hint

        user = users[0]
        if _is_valid_user_email(user.email):
            return existing_hint

        user.email = desired_email
        await db.commit()
        await db.refresh(user)

    if existing_hint:
        existing_hint = {
            **existing_hint,
            "email": desired_email,
        }
        info_path = get_first_run_file_path()
        info_path.parent.mkdir(parents=True, exist_ok=True)
        info_path.write_text(json.dumps(existing_hint, ensure_ascii=True, indent=2), encoding="utf-8")

    logger.warning("Email do admin desktop local corrigido para um endereco compativel com validacao.")
    return existing_hint


async def _ensure_initial_admin() -> dict[str, str] | None:
    existing_hint = load_initial_admin_info()
    engine = get_async_engine()
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as db:
        user = (await db.execute(select(User).order_by(User.id).limit(1))).scalar_one_or_none()
        if user:
            return existing_hint

        admin_info = DesktopInitialAdmin(
            email=_resolve_admin_email(),
            password=_resolve_admin_password(),
            full_name=_resolve_admin_full_name(),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        db.add(
            User(
                username="admin",
                email=admin_info.email,
                hashed_password=get_password_hash(admin_info.password),
                full_name=admin_info.full_name,
                is_superuser=True,
                is_active=True,
                is_verified=True,
                allowed_tabs=[],
            )
        )
        await db.commit()

    info_path = get_first_run_file_path()
    info_path.parent.mkdir(parents=True, exist_ok=True)
    info_path.write_text(
        json.dumps(admin_info.to_dict(), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    logger.info("Usuario administrador inicial criado para o desktop local")
    return admin_info.to_dict()


async def bootstrap_desktop_database() -> dict[str, str] | None:
    if not is_desktop_mode():
        return None

    data_dir = get_desktop_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    sqlite_db_path = _get_sqlite_database_path()
    is_new_sqlite_database = sqlite_db_path is not None and not sqlite_db_path.exists()

    try:
        if not is_new_sqlite_database and _sqlite_schema_needs_alembic_stamp():
            logger.warning(
                "Banco desktop local existente sem revisao Alembic valida detectado; marcando schema atual como head.",
            )
            _stamp_alembic_head()

        _run_alembic_migrations()
    except Exception as exc:
        if not is_new_sqlite_database:
            raise

        logger.warning(
            "Falha ao aplicar Alembic no banco desktop novo; usando create_all como fallback. Erro: %s",
            exc,
        )
        await _fallback_create_schema()

    await _repair_desktop_admin_identity()
    return await _ensure_initial_admin()
