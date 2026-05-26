import logging
import os
import json
import urllib.request
import urllib.error
from queue import Queue, Empty
from threading import Thread

class LokiQueueHandler(logging.Handler):
    """
    Handler que envia logs para o Grafana Loki via HTTP.
    Usa uma fila em background para não bloquear a aplicação.
    Só ativa se a variável de ambiente LOKI_URL estiver definida.
    """

    def __init__(self, loki_url: str):
        super().__init__()
        self.loki_url = loki_url.rstrip("/") + "/loki/api/v1/push"
        self.queue = Queue()
        self._worker = Thread(target=self._processar_fila, daemon=True)
        self._worker.start()

    def emit(self, record: logging.LogRecord):
        try:
            self.queue.put_nowait(record)
        except Exception:
            pass

    def _processar_fila(self):
        while True:
            try:
                record = self.queue.get(timeout=1)
                self._enviar(record)
            except Empty:
                continue
            except Exception:
                continue

    def _enviar(self, record: logging.LogRecord):
        try:
            mensagem = self.format(record)
            #timestamp em nanosegundos para Loki
            timestamp_ns = str(int(record.created * 1e9))
            payload = {
                "streams": [
                    {
                        "stream": {
                            "service": "vrumvrum",
                            "level": record.levelname.lower(),
                        },
                        "values": [[timestamp_ns, mensagem]],
                    }
                ]
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.loki_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            pass #nunca deixa erro de log derrubar a aplicacao

def configurar_loki():                                             
    """
    Adiciona o LokiQueueHandler se LOKI_URL estiver definida.
    Chamado dentro do setup_logging().
    """
    loki_url = os.getenv("LOKI_URL")
    if not loki_url:
        return

    handler = LokiQueueHandler(loki_url)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
