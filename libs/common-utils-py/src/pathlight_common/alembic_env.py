"""
Alembic environment configuration for Pathlight services.
This module provides a reusable alembic env.py configuration that can be used across all services.
"""

from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

def setup_alembic_env(target_metadata, models_module=None):
    """
    Setup Alembic environment for a Pathlight service.
    
    Args:
        target_metadata: SQLAlchemy metadata object (usually Base.metadata)
        models_module: Optional module to import to ensure all models are loaded
    """
    # Load environment variables
    from pathlight_common import get_database_url
    
    # Get alembic config
    config = context.config
    
    # Set database URL from environment
    database_url = get_database_url()
    config.set_main_option("sqlalchemy.url", database_url)
    
    # Import models if provided
    if models_module:
        import importlib
        importlib.import_module(models_module)
    
    # Interpret the config file for Python logging
    if config.config_file_name is not None:
        fileConfig(config.config_file_name)

    def run_migrations_offline() -> None:
        """Run migrations in 'offline' mode."""
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
        """Run migrations in 'online' mode."""
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection, target_metadata=target_metadata
            )

            with context.begin_transaction():
                context.run_migrations()

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
