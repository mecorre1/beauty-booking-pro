"""Alembic environment: uses app settings, optional injected connection (tests)."""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool, text

# Backend root on sys.path (alembic.ini prepend_sys_path = . assumes cwd is backend/)
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from app.config import settings  # noqa: E402

import app.models  # noqa: E402, F401 — register metadata
from app.db import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sqlite_connect_args() -> dict:
    return {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}


def _enable_sqlite_fk(connection) -> None:
    if connection.dialect.name == "sqlite":
        connection.execute(text("PRAGMA foreign_keys=ON"))


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    injected: object | None = config.attributes.get("connection")

    if injected is not None:
        connection = injected
        _enable_sqlite_fk(connection)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
        return

    connectable = create_engine(
        settings.database_url,
        connect_args=_sqlite_connect_args(),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _enable_sqlite_fk(connection)
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
