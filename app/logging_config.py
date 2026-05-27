from app.logging_handlers import configurar_loki
import logging
import os
import sys
import structlog

def setup_logging():
    """Configura o structlog para saída em JSON estruturado."""

    #LOG_LEVEL configurável (vai permitir DEBUG em desenvolvimento)
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    #capturar logs do uvicorn no mesmo formato JSON
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True

    # config o logging padrão do python
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        stream=sys.stdout,
    )
    #processor de exceções estruturadas (captura e trata exceções no fluxo do programa)
    #config o structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.contextvars.merge_contextvars,
            #stack traces em JSON
            structlog.processors.format_exc_info,
            #JSON
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    #handler para loki se LOKI_URL estiver definida
    configurar_loki()

def get_logger(name: str = "vrumvrum"):
    """Retorna um logger configurado com o nome do serviço."""
    return structlog.get_logger(name)

def log_estruturado(
        evento: str,
        corrida_id: str | None = None,
        estado_anterior: str | None = None,
        estado_novo: str | None = None,
        lamport_clock: int | None = None,
        nivel: str = "INFO",
        extras: dict | None = None,
) -> None:
    logger = get_logger()

    campos = {
        "corrida_id": corrida_id,
        "estado_anterior": estado_anterior,
        "estado_novo": estado_novo,
        "lamport_clock": lamport_clock,
    }

    if extras:
        campos.update(extras)

    campos = {k: v for k, v in campos.items() if v is not None}

    #seleciona nivel correto
    nivel =  nivel.upper()
    if nivel in ("WARNING", "WARN"):
        logger.warning(evento, **campos)
    elif nivel == "ERROR":
        logger.error(evento, **campos)
    else:
        logger.info(evento, **campos)
