# Arquivo de testes da auditoria de corridas

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

# Definição do teste de aquisição de corrida
@pytest.mark.asyncio
async def test_get_ride():

    transport = ASGITransport(app = app)

    async with AsyncClient(transport = transport, base_url = "https://test_get_ride") as ac:

        # Criação de uma corrida teste
        create_ride_response = await ac.post("/rides/", json={
            "passenger_id": "passageiro teste",
            "origin": {
                "lat": -18.00, "lng": -18.00,
                "street": "Rua teste", "number": "1",
                "city": "Rio Paranaíba", "state": "MG"
            },
            "destination": {
                "lat": -19.00, "lng": -20.00,
                "street": "Rua teste", "number": "2",
                "city": "Rio Paranaíba", "state": "MG"
            }
        })

        # Verifica se a corrida foi inserida com sucesso
        assert create_ride_response.status_code == 200

        # Adquire a corrida
        response = await ac.get(f"audit/rides/{create_ride_response.json()["id"]}")

    # Verifica se a aquisição foi sucedida
    assert response.status_code == 200

    # Verifica se os IDs das corridas são o mesmo
    assert response.json()["ride_id"] == create_ride_response.json()["id"]