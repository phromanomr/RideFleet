from contextlib import asynccontextmanager
import uuid
from fastapi import FastAPI, Request
import structlog
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

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Bind de um UUID único a cada requisição para correlação de logs."""
    request_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

app.include_router(rides.router)
app.include_router(audit.router)
app.include_router(drivers.router)
app.include_router(health.router)


