"""Alembic environment configuration for ICFES Leveling database migrations."""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add project's 'apps/backend' directory to path for imports
backend_app_path = str(Path(__file__).parent.parent.parent / 'apps' / 'backend')
if backend_app_path not in sys.path:
    sys.path.insert(0, backend_app_path)


try:
    # Import models for autogenerate
    from app.core.database import Base
    from app.models import *  # Import all models
    target_metadata = Base.metadata
except ImportError as e:
    print(f"Warning: Could not import models for autogenerate: {e}")
    target_metadata = None

# This is the Alembic Config object
config = context.config

# Override database URL from environment if available
database_url = os.getenv('DATABASE_URL')
if database_url:
    config.set_main_option('sqlalchemy.url', database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def include_object(object, name, type_, reflected, compare_to):
    """Filter objects to include in migrations."""
    if type_ == "table" and name in ["alembic_version"]:
        return False
    if type_ == "table" and (name.endswith("_backup_") or "_backup_" in name):
        return False
    return True

def compare_type(context, inspected_column, metadata_column, 
                inspected_type, metadata_type):
    """Compare column types for changes."""
    return None

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=compare_type,
        render_as_batch=False,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = config.get_main_option("sqlalchemy.url")
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=compare_type,
            render_as_batch=False,
            compare_server_default=True,
            include_schemas=False,
            user_module_prefix='sqlalchemy.',
            transaction_per_migration=False,
        )

        with context.begin_transaction():
            # Log migration start
            # CORRECTED: get_head_revision() is the correct function name
            # CORRECTED: get_head_revision() is the correct function name
            head_rev = context.get_head_revision()
            # context.execute("-- Migration started at %s" % head_rev)
            
            context.run_migrations()
            
            # Log migration end
            # CORRECTED: get_head_revision() is the correct function name
            head_rev_after = context.get_head_revision()
            # context.execute("-- Migration completed at %s" % head_rev_after)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()