import time

corridas_inicio = {}
latencias = []

total_erros = 0
total_sucessos = 0


def registrar_inicio_corrida(corrida_id: str):
    corridas_inicio[corrida_id] = time.time()


def registrar_fim_corrida(corrida_id: str):
    if corrida_id in corridas_inicio:
        tempo_total = (
            time.time() - corridas_inicio[corrida_id]
        ) * 1000
        latencias.append(tempo_total)
        del corridas_inicio[corrida_id]


def registrar_erro():
    global total_erros
    total_erros += 1


def registrar_sucesso():
    global total_sucessos
    total_sucessos += 1


def calcular_latencia_media():
    if not latencias:
        return 0
    return round(sum(latencias) / len(latencias), 2)


def calcular_taxa_erro():
    total = total_erros + total_sucessos
    if total == 0:
        return 0
    return round(total_erros / total, 2)