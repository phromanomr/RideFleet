# tests/test_contract.py

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app

# JSON padrão que o Core envia para o leilão
INCOMING_PAYLOAD = {
    "rideUuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "origin": {
        "lat": -20.7546, "lng": -42.8825,
        "street": "Av. P.H. Rolfs", "number": "S/N",
        "city": "Viçosa", "state": "MG"
    },
    "destination": {
        "lat": -20.7546, "lng": -42.8825,
        "street": "Av. P.H. Rolfs", "number": "S/N",
        "city": "Viçosa", "state": "MG"
    },
    "originServiceId": "group-a",
    "passengerId": "passenger-42",
    "passengerName": "João Silva",
    "logicalTimestamp": 18,
    "auctionDeadline": "2026-12-31T23:59:59Z"
}

# JSON padrão que o Core envia quando atribui a corrida
ASSIGNED_PAYLOAD = {
    "rideUuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "origin": {
        "lat": -20.7546, "lng": -42.8825,
        "street": "Av. P.H. Rolfs", "number": "S/N",
        "city": "Viçosa", "state": "MG"
    },
    "destination": {
        "lat": -20.7546, "lng": -42.8825,
        "street": "Av. P.H. Rolfs", "number": "S/N",
        "city": "Viçosa", "state": "MG"
    },
    "passengerId": "passenger-42",
    "passengerName": "João Silva",
    "originServiceId": "group-a",
    "logicalTimestamp": 31,
    "lockExpiresAt": "2026-12-31T23:59:59Z"
}


@pytest.fixture(autouse=True)
def mock_rabbitmq():
    """Mocka o RabbitMQ para não precisar dele nos testes."""
    with patch("app.services.rabbitmq_service.init_rabbitmq", new_callable=AsyncMock), \
         patch("app.services.rabbitmq_service.close_rabbitmq", new_callable=AsyncMock), \
         patch("app.services.rabbitmq_service.consumir_fila_entrada", new_callable=AsyncMock), \
         patch("app.services.rabbitmq_service.consumir_fila_saida", new_callable=AsyncMock):
        yield


@pytest.fixture(autouse=True)
def mock_core_service():
    """Mocka chamadas ao Core para não precisar dele nos testes."""
    with patch("app.routers.core.atualizar_status", new_callable=AsyncMock) as mock:
        mock.return_value = {"state": "confirm"}
        yield mock


# ─────────────────────────────────────────────
# Testes do POST /rides/incoming
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_incoming_com_motorista_disponivel():
    """Com motorista disponível deve retornar 200 com proposta válida."""
    with patch(
        "app.routers.core.tem_motorista_disponivel",
        new_callable=AsyncMock,
        return_value=True
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post("/rides/incoming", json=INCOMING_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert "estimatedEta" in body
    assert "estimatedPrice" in body
    assert "logicalTimestamp" in body
    assert isinstance(body["estimatedEta"], int)
    assert isinstance(body["estimatedPrice"], float)
    assert body["logicalTimestamp"] > 0


@pytest.mark.asyncio
async def test_incoming_sem_motorista_disponivel():
    """Sem motorista disponível deve retornar 204 sem body."""
    with patch(
        "app.services.ride_service.tem_motorista_disponivel",
        new_callable=AsyncMock,
        return_value=False
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post("/rides/incoming", json=INCOMING_PAYLOAD)

    assert response.status_code == 204
    assert response.content == b""


# ─────────────────────────────────────────────
# Testes do POST /rides/{rideUuid}/assigned
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_assigned_retorna_accepted():
    """Atribuição válida deve retornar 200 com status accepted."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        response = await ac.post(
            f"/rides/{ASSIGNED_PAYLOAD['rideUuid']}/assigned",
            json=ASSIGNED_PAYLOAD
        )

    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}


@pytest.mark.asyncio
async def test_assigned_sincroniza_relogio(mock_core_service):
    """Após atribuição o relógio de Lamport deve ser maior que o recebido."""
    from app.distributed.logical_clock import lamport

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        await ac.post(
            f"/rides/{ASSIGNED_PAYLOAD['rideUuid']}/assigned",
            json=ASSIGNED_PAYLOAD
        )

    # logicalTimestamp enviado foi 31, o nosso deve ser >= 32
    assert lamport.value >= ASSIGNED_PAYLOAD["logicalTimestamp"] + 1