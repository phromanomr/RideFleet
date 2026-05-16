import os
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base

# 1. Defina a URL do seu banco de TESTES do Postgres.
# Mude "vrumvrum" para "vrumvrum_test" (ou outro nome) para não apagar seus dados reais!
SQLALCHEMY_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/vrumvrum_test"
)

# 2. Cria o engine sem as configurações antigas do SQLite
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False
)

TestSession = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

@pytest.fixture(autouse=True)
async def setup_database():
    # Cria a estrutura de tabelas no banco de testes
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield # Executa os testes
    
    # Destrói as tabelas ao final (limpa o banco para o próximo teste)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture(autouse=True)
def override_db_session():
    async def _override_get_db():
        async with TestSession() as session:
            yield session

    # Substitui a dependência do FastAPI pelo nosso banco de testes
    app.dependency_overrides[get_db] = _override_get_db
    yield
    # Limpa a substituição
    app.dependency_overrides.clear()