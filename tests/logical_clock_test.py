# Arquivo de teste do relogio lógico

import pytest
import asyncio
from app.distributed.logical_clock import LamportClock, lamport, _audit_log, log_event, get_audit_log

# Teste de inicialização do relogio lógico
@pytest.mark.asyncio
async def test_lamport_clock_initial_state():
    clock = LamportClock()
    assert clock.value == 0

# Teste de tick
@pytest.mark.asyncio
async def test_lamport_clock_tick():
    clock = LamportClock()
    
    val1 = await clock.tick()

    assert val1 == 1
    assert clock.value == 1

    val2 = await clock.tick()

    assert val2 == 2
    assert clock.value == 2

# Teste de atribuição de tick
@pytest.mark.asyncio
async def test_lamport_clock_receive():
    clock = LamportClock()
    await clock.tick()  

    val = await clock.receive(0)
    assert val == 2
    assert clock.value == 2

    val = await clock.receive(10)
    assert val == 11
    assert clock.value == 11

# Teste de concorrencia
@pytest.mark.asyncio
async def test_lamport_clock_concurrency():
    clock = LamportClock()
    
    await asyncio.gather(*(clock.tick() for _ in range(100)))
    
    assert clock.value == 100

# Teste de log de eventos
@pytest.mark.asyncio
async def test_log_event():
    ride_id = "corrida teste"
    
    clock1 = await log_event(ride_id, "RIDE_REQUESTED")
    clock2 = await log_event(ride_id, "RIDE_ACCEPTED", {"driver_id": "motorista teste"})
    
    assert clock1 == 1
    assert clock2 == 2
    assert len(_audit_log) == 2
    
    assert _audit_log[0].event_type == "RIDE_REQUESTED"
    assert _audit_log[1].details == {"driver_id": "motorista teste"}

# Teste de auditoria de logs
@pytest.mark.asyncio
async def test_get_audit_log():
    
    # Criação de logs de evento
    await log_event("corrida A", "EVENT_1")
    await log_event("corrida B", "EVENT_X")
    await log_event("corrida A", "EVENT_2")
    
    # Embaralhamento da lista
    _audit_log.reverse()
    
    # Verificação da aquisição de log de corridas
    logs = get_audit_log("corrida A")
    assert len(logs) == 2
    
    # Teste de atribuição de ticks
    assert logs[0]["event_type"] == "EVENT_1"
    assert logs[0]["lamport_clock"] == 1
    
    assert logs[1]["event_type"] == "EVENT_2"
    assert logs[1]["lamport_clock"] == 3

    # Garante a presença do timestamp e identificador de serviço nos logs
    assert "timestamp" in logs[0]
    assert logs[0]["service"] == "vrumvrum"