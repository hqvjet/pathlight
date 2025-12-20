from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Load .env so DATABASE_URL and other config are available for Alembic
try:
    from dotenv import load_dotenv
    for env_path in [
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        ".env",
    ]:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            break
except ImportError:
    pass

# Cho phép import src.models và (tùy chọn) config trong src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from src.models import Base  # metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Đọc DATABASE_URL từ env hoặc alembic.ini (ưu tiên env, fallback ini)
target_metadata = Base.metadata
db_url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")

def run_migrations_offline():
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="quiz_alembic_version",
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": db_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="quiz_alembic_version",
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()