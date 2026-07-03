import time
from prometheus_client import Counter, Histogram, Gauge
from app.config import ORIGIN_SERVICE_ID

# ---------------------------------------------------------------------------
# Métricas Prometheus
# Counter   → só sobe (total de corridas, erros, sucessos)
# Histogram → distribui valores em buckets (latência por corrida)
# Gauge     → sobe e desce (fila atual, motoristas disponíveis)
# ---------------------------------------------------------------------------

locks_acquired_total = Counter(
    "ridefleet_locks_acquired_total", 
    "Total de locks adquiridos", 
    ["service"]
)
locks_expired_total = Counter(
    "ridefleet_locks_expired_total", 
    "Total de locks perdidos ou expirados", 
    ["service"]
)

def registrar_lock_adquirido():
    locks_acquired_total.labels(service=ORIGIN_SERVICE_ID).inc()

def registrar_lock_expirado():
    locks_expired_total.labels(service=ORIGIN_SERVICE_ID).inc()

saga_transitions_total = Counter(
    "ridefleet_saga_transitions_total", 
    "Transições de estado na Saga", 
    ["from_state", "to_state", "service"]
)
saga_compensations_total = Counter(
    "ridefleet_saga_compensations_total", 
    "Compensações acionadas na Saga", 
    ["service"]
)

def registrar_transicao_saga(from_state: str, to_state: str):
    saga_transitions_total.labels(from_state=from_state, to_state=to_state, service=ORIGIN_SERVICE_ID).inc()

def registrar_compensacao_saga():
    saga_compensations_total.labels(service=ORIGIN_SERVICE_ID).inc()

circuit_breaker_state = Gauge(
    "ridefleet_circuit_breaker_state", 
    "Estado do CB (0=CLOSED, 1=OPEN, 2=HALF_OPEN)", 
    ["service"]
)

def atualizar_circuit_breaker(estado: int):
    # Por padrão, inicie com 0 (CLOSED) se ainda não implementou a lógica de falhas
    circuit_breaker_state.labels(service=ORIGIN_SERVICE_ID).set(estado)

corridas_delegadas_total = Counter(
    "ridefleet_rides_delegated_total", 
    "Corridas delegadas ao Core", 
    ["service"]
)
corridas_locais_total = Counter(
    "ridefleet_rides_local_total", 
    "Corridas resolvidas internamente", 
    ["service"]
)

def registrar_corrida_local():
    corridas_locais_total.labels(service=ORIGIN_SERVICE_ID).inc()

def registrar_corrida_delegada():
    corridas_delegadas_total.labels(service=ORIGIN_SERVICE_ID).inc()

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "Latência dos endpoints HTTP",
    ["handler", "method", "service"]
)

corridas_total = Counter(
    "vrumvrum_corridas_total",
    "Total de corridas processadas",
    ["resultado"],          # label: "sucesso" ou "erro"
)

corrida_duracao = Histogram(
    "vrumvrum_corrida_duracao_ms",
    "Duração de cada corrida em milissegundos",
    buckets=[500, 1000, 5000, 10000, 30000, 60000],
)

fila_tamanho = Gauge(
    "vrumvrum_fila_tamanho",
    "Número de corridas aguardando na fila do RabbitMQ",
)

motoristas_disponiveis = Gauge(
    "vrumvrum_motoristas_disponiveis",
    "Número de motoristas disponíveis no momento",
)

corridas_por_status = Gauge(
    "vrumvrum_corridas_por_status",
    "Número de corridas agrupadas por status atual",
    ["status"],   # label: "matched", "confirmed", "in_transit", "completed", etc.
)

# ---------------------------------------------------------------------------
# Dicionário interno para calcular duração por corrida
# ---------------------------------------------------------------------------
_corridas_inicio: dict = {}


def registrar_inicio_corrida(corrida_id: str):
    """Marca o instante de início de uma corrida."""
    _corridas_inicio[corrida_id] = time.time()


def registrar_fim_corrida(corrida_id: str):
    """Calcula e registra a duração da corrida no Histogram."""
    if corrida_id in _corridas_inicio:
        duracao_ms = (time.time() - _corridas_inicio[corrida_id]) * 1000
        corrida_duracao.observe(duracao_ms)
        del _corridas_inicio[corrida_id]


def registrar_erro():
    """Incrementa o counter de corridas com resultado 'erro'."""
    corridas_total.labels(resultado="erro").inc()


def registrar_sucesso():
    """Incrementa o counter de corridas com resultado 'sucesso'."""
    corridas_total.labels(resultado="sucesso").inc()


def atualizar_fila(tamanho: int):
    """Atualiza o gauge com o tamanho atual da fila (chamado pelo health check)."""
    fila_tamanho.set(tamanho)


def atualizar_motoristas(quantidade: int):
    """Atualiza o gauge com o número de motoristas disponíveis."""
    motoristas_disponiveis.set(quantidade)


def atualizar_corridas_por_status(contagem_por_status: dict):
    """
    Atualiza o gauge de corridas por status.
    Recebe um dict como {"matched": 2, "in_transit": 1, "completed": 5}.
    Chamado pelo health check após consultar o banco.
    """
    for status, quantidade in contagem_por_status.items():
        corridas_por_status.labels(status=status).set(quantidade)


# ---------------------------------------------------------------------------
# Funções legadas mantidas para não quebrar código que já as usa
# ---------------------------------------------------------------------------
def calcular_latencia_media() -> float:
    """Compatibilidade com health.py — retorna média das amostras do histogram."""
    samples = corrida_duracao.collect()
    for metric in samples:
        for sample in metric.samples:
            if sample.name == "vrumvrum_corrida_duracao_ms_sum":
                total = sample.value
            if sample.name == "vrumvrum_corrida_duracao_ms_count":
                count = sample.value
    try:
        return round(total / count, 2) if count else 0
    except Exception:
        return 0


def calcular_taxa_erro() -> float:
    """Compatibilidade com health.py — recalcula a taxa de erro atual."""
    erros = 0
    sucessos = 0
    for metric in corridas_total.collect():
        for sample in metric.samples:

            if not sample.name.endswith("_total"):
                continue
            
            if sample.labels.get("resultado") == "erro":
                erros += sample.value
            elif sample.labels.get("resultado") == "sucesso":
                sucessos += sample.value
    total = erros + sucessos
    return round(erros / total, 2) if total != 0 else 0

corridas_recebidas_total = Counter(
    "ridefleet_rides_received_total",
    "Total de corridas recebidas de outros grupos"
)
servico_estado = Gauge(
    "vrumvrum_servico_estado",
    "Estado atual do servico: 0=UP, 1=DEGRADED, 2=DOWN"
)
fila_saida_tamanho = Gauge(
    "vrumvrum_fila_saida_tamanho",
    "Numero de corridas aguardando delegacao ao Core (fila de saida)"
)
requisicoes_por_instancia = Counter(
    "vrumvrum_requisicoes_por_instancia",
    "Total de requisicoes por instancia da API",
    ["instance_id"]
)

def registrar_corrida_recebida():
    corridas_recebidas_total.inc()

def atualizar_estado_servico(status: str):
    mapa = {"UP": 0, "DEGRADED": 1, "DOWN": 2}
    servico_estado.set(mapa.get(status, 2))

def atualizar_fila_saida(tamanho: int):
    fila_saida_tamanho.set(tamanho)

def registrar_requisicao(instance_id: str):
    requisicoes_por_instancia.labels(instance_id=instance_id).inc()

locks_acquired_total.labels(service=ORIGIN_SERVICE_ID).inc(0)
locks_expired_total.labels(service=ORIGIN_SERVICE_ID).inc(0)
circuit_breaker_state.labels(service=ORIGIN_SERVICE_ID).set(0)
corridas_delegadas_total.labels(service=ORIGIN_SERVICE_ID).inc(0)
corridas_locais_total.labels(service=ORIGIN_SERVICE_ID).inc(0)
saga_compensations_total.labels(service=ORIGIN_SERVICE_ID).inc(0)
saga_transitions_total.labels(from_state="match", to_state="confirm", service=ORIGIN_SERVICE_ID).inc(0)
saga_transitions_total.labels(from_state="confirm", to_state="in_transit", service=ORIGIN_SERVICE_ID).inc(0)
saga_transitions_total.labels(from_state="in_transit", to_state="complete", service=ORIGIN_SERVICE_ID).inc(0)
corridas_total.labels(resultado="erro").inc(0)
corridas_total.labels(resultado="sucesso").inc(0)