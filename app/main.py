from contextlib import asynccontextmanager
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import structlog
from app.routers import rides, audit, drivers, health, core, geo_service
from app.logging_config import setup_logging, get_logger
from app.services.rabbitmq_service import init_rabbitmq, close_rabbitmq, consumir_fila_entrada, consumir_fila_saida
from app.services.core_service import registrar_core
from fastapi.middleware.cors import CORSMiddleware
from app.config import ORIGIN_SERVICE_ID
import time
import os

# configura o logging ao iniciar
setup_logging()
logger = get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # exe ao iniciar
    logger.info("servico_iniciado", servico="vrumvrum", version="1.0.0")

    await registrar_core()
    
    await init_rabbitmq()

    # Registra o worker que vai processar as mensagens da fila de entrada no background
    # A importação da função é feita aqui dentro para evitar problemas de importação circular
    from app.services.ride_service import processar_corrida_da_fila, processar_corrida_saida
    await consumir_fila_entrada(processar_corrida_da_fila)
    await consumir_fila_saida(processar_corrida_saida)
    yield
    await close_rabbitmq()
    # exe ao encerrar
    logger.info("servico_encerrado", servico="vrumvrum")

app = FastAPI(
    title="VrumVrum",
    description="Serviço de transporte distribuído - SIN 142 UFV-CRP 2026/1",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Bind de um UUID único a cada requisição para correlação de logs."""
    request_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    from app import metrics
    metrics.registrar_requisicao(os.getenv("INSTANCE_ID", "unknown"))

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

app.include_router(rides.router)
app.include_router(audit.router)
app.include_router(drivers.router)
app.include_router(health.router)
app.include_router(core.router)
app.include_router(geo_service.router)

# ---------------------------------------------------------------------------
# Endpoint /metrics — formato Prometheus (texto puro)
# O Prometheus raspa esse endpoint a cada 10s conforme prometheus.yml
# ---------------------------------------------------------------------------
@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

# ---------------------------------------------------------------------------
# Middleware de observabilidade
# Registra métricas Prometheus e alimenta o Health Check (Latência e Erros)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    from app import metrics
    
    inicio = time.time()
    status_code = 500 # Fallback caso a requisição estoure um erro não tratado

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response

    finally:
        duracao_s = time.time() - inicio
        duracao_ms = duracao_s * 1000

        # Alimenta as métricas de Health Check antigas
        metrics.corrida_duracao.observe(duracao_ms)
        if status_code >= 400:
            metrics.registrar_erro()
        else:
            metrics.registrar_sucesso()

        # NOVA MÉTRICA EXIGIDA: Grava a duração padronizada
        metrics.http_request_duration_seconds.labels(
            handler=request.url.path,
            method=request.method,
            service=ORIGIN_SERVICE_ID
        ).observe(duracao_s)