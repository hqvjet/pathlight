from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy import create_engine
from alembic import context

from src.core.settings import get_settings
from src.core.database import Base
from src import models  # noqa

config = context.config
fileConfig(config.config_file_name)
settings = get_settings()

config.set_main_option("sqlalchemy.url", settings.postgres_dsn)

def run_migrations_offline() -> None:
    url = settings.postgres_dsn
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = create_engine(settings.postgres_dsn, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
