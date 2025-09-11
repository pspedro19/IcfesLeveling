"""Alembic environment configuration for ICFES Leveling database migrations."""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    # Import models for autogenerate
    from apps.backend.app.core.database import Base
    from apps.backend.app.models import *  # Import all models
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
    # Skip certain tables or objects if needed
    if type_ == "table" and name in ["alembic_version"]:
        return False
    
    # Skip temporary tables
    if type_ == "table" and (name.endswith("_backup_") or "_backup_" in name):
        return False
    
    return True

def compare_type(context, inspected_column, metadata_column, 
                inspected_type, metadata_type):
    """Compare column types for changes."""
    # Handle PostgreSQL specific type comparisons
    return None

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
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
        include_object=include_object,
        compare_type=compare_type,
        # Additional configuration for better migrations
        render_as_batch=False,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    
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
            # Additional configuration for better migrations
            render_as_batch=False,
            compare_server_default=True,
            # Handle constraints and indexes properly
            include_schemas=False,
            # PostgreSQL specific options
            user_module_prefix='sqlalchemy.',
            # Migration options
            transaction_per_migration=True,
        )

        # Execute pre-migration hooks
        with context.begin_transaction():
            # Log migration start
            context.execute("-- Migration started at %s" % 
                          context.get_current_revision())
            
            context.run_migrations()
            
            # Log migration end
            context.execute("-- Migration completed at %s" % 
                          context.get_current_revision())


# Determine which mode to run
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()