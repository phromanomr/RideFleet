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
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

def get_logger(name: str = "vrumvrum"):
    """Retorna um logger configurado com o nome do serviço."""
    return structlog.get_logger(name)
