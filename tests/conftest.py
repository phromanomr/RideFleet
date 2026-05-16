# Arquivo para a definição de fixtures (usado para inicializar funções de teste) que serão 
# executadas antes do inicio dos testes.
# Caso todos os testes falhem então o erro está provavelmente aqui.

import os
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base
from app.distributed.logical_clock import lamport, _audit_log

# Definição da URL do banco de dados de teste
SQLALCHEMY_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/vrumvrum_test"
)

# Criação do engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False
)

TestSession = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

# Fixture para criação do setup do banco
@pytest.fixture(autouse=True)
async def setup_database():
    # Cria a estrutura de tabelas no banco de testes com base no do serviço
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Executa os testes
    yield 
    
    # Destrói as tabelas, garantindo que os dados de teste não persistam
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Finalizar a engine
    await engine.dispose()

# Fixture para sobreescrever a função de sessão do banco de dados
@pytest.fixture(autouse=True)
def override_db_session():
    async def _override_get_db():
        async with TestSession() as session:
            yield session

    # Substitui a dependência do FastAPI pelo banco de dados de teste
    app.dependency_overrides[get_db] = _override_get_db

    # Executa 
    yield

    # Limpa a substituição
    app.dependency_overrides.clear()

# Fixture para resetar log de auditoria e relogio lógico
@pytest.fixture(autouse=True)
def reset_globals():
    _audit_log.clear()
    lamport._clock = 0