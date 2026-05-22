from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import rides, audit, drivers, health
from app.logging_config import setup_logging, get_logger

from app.services.rabbitmq_service import init_rabbitmq, close_rabbitmq, consumir_fila_entrada

# configura o logging ao iniciar
setup_logging()
logger = get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # exe ao iniciar
    logger.info("servico_iniciado", servico="vrumvrum", version="1.0.0")

    await init_rabbitmq()
    
    # 2. Registra o worker que vai processar as mensagens da fila de entrada no background
    # A importação da função é feita aqui dentro para evitar problemas de importação circular
    from app.services.ride_service import processar_corrida_da_fila
    await consumir_fila_entrada(processar_corrida_da_fila)

    yield

    await close_rabbitmq()
    # exe ao encerrar
    logger.info("servico_encerrado", servico="vrumvrum")
app = FastAPI(
    title="VrumVrum",
    description="Serviço de transporte distribuído -  SIN 142 UFV-CRP 2026/1",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(rides.router)
app.include_router(audit.router)
app.include_router(drivers.router)
app.include_router(health.router)


