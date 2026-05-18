import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# importa
from app.database import Base
from app.models.ride_model import RideModel  # noqa: F401
from app.models.driver_model import DriverModel 

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Roda migrations sem conexão real — gera SQL puro."""
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Roda migrations com conexão real ao banco."""
    import os
    db_url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")

    connectable = create_async_engine(db_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())