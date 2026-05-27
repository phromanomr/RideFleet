import time
from prometheus_client import Counter, Histogram, Gauge

# ---------------------------------------------------------------------------
# Métricas Prometheus
# Counter   → só sobe (total de corridas, erros, sucessos)
# Histogram → distribui valores em buckets (latência por corrida)
# Gauge     → sobe e desce (fila atual, motoristas disponíveis)
# ---------------------------------------------------------------------------

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
            if sample.labels.get("resultado") == "erro":
                erros = sample.value
            elif sample.labels.get("resultado") == "sucesso":
                sucessos = sample.value
    total = erros + sucessos
    return round(erros / total, 2) if total else 0