import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# This is the Alembic Config object, which provides
# access to values within the .ini file in use.
config = context.config

# Interpret the config file for Python's standard logging.
# This uses the default logging.conf provided by Alembic.
fileConfig(config.config_file_name)

# Add your project's root directory to sys.path.
# This ensures that your Flask application's modules (like 'qr_code_genius')
# can be imported correctly by Alembic.
# Assumes the project structure:
# project_root/
# ├── qr_code_genius/
# │   ├── __init__.py (contains create_app, db)
# │   └── models.py
# └── migrations/
#     └── env.py
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, project_root)

# Import the Flask application factory and its SQLAlchemy instance.
# This assumes `create_app` and `db` are defined in `qr_code_genius/__init__.py`.
try:
    from qr_code_genius import create_app, db
    # Create an app instance to access its configuration and SQLAlchemy object.
    # This instance is used to retrieve the database URI and metadata.
    app = create_app()
except ImportError as e:
    raise ImportError(
        f"Could not import Flask app or db instance from 'qr_code_genius'. "
        f"Ensure 'qr_code_genius' package is accessible and contains create_app() and db. Error: {e}"
    )

# target_metadata should be imported from your model module.
# For Flask-SQLAlchemy, this is typically `db.Model.metadata`.
# This object holds the collection of all table objects (models) defined in your application.
target_metadata = db.Model.metadata

# Override the 'sqlalchemy.url' option in Alembic's configuration.
# This ensures that Alembic uses the same database URI as configured in the Flask application,
# promoting consistency and avoiding redundant configuration.
with app.app_context():
    database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    if not database_url:
        raise ValueError(
            "SQLALCHEMY_DATABASE_URI not found in Flask app configuration. "
            "Please ensure it's set in your Flask app's config (e.g., config.py or environment variables)."
        )
    config.set_main_option('sqlalchemy.url', database_url)


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    By skipping the Engine creation, we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the script output.
    This mode is useful for generating SQL scripts that can be applied manually.
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


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario, we need to create an Engine and associate a connection
    with the context. This mode connects to the actual database and applies
    migrations directly.
    """
    # It's crucial to run online migrations within the Flask application context.
    # This ensures that all SQLAlchemy models are loaded and registered with
    # `db.Model.metadata`, which Alembic uses to compare against the database schema.
    with app.app_context():
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,  # Alembic manages its own connections, so no pooling needed.
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata
            )

            with context.begin_transaction():
                context.run_migrations()


# Determine whether to run in offline or online mode based on Alembic's context.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()