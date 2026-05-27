import logging
import structlog

def setup_logging():
    """Configura o structlog para saída em JSON estruturado."""

    # config o logging padrão do python
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )

    #config o structlog
    structlog.configure(
        processors=[
            #nivel
            structlog.stdlib.add_log_level,
            #timestamp em iso
            structlog.processors.TimeStamper(fmt="iso"),
            #add nome do serviço
            structlog.contextvars.merge_contextvars,
            #JSON
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

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
        "servico": "vrumvrum",
        "corrida_id": corrida_id,
        "estado_anterior": estado_anterior,
        "estado_novo": estado_novo,
        "lamport_clock": lamport_clock,
    }

    #add campos extras se existirem
    if extras:
            campos.update(extras)

    campos = {k: v for k, v in campos.items() if v is not None}

    #seleciona nivel correto
    nivel =  nivel.upper()
    if nivel == "WARNING" or nivel == "WARN":
        logger.warning(evento, **campos)
    elif nivel == "ERROR":
        logger.error(evento, **campos)
    else:
        logger.info(evento, **campos)