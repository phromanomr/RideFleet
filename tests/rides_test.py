# Arquivo de testes do endpoint de corridas

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

# Verificação da criação e aquisição de corridas
@pytest.mark.asyncio
async def test_rides():
    
    transport = ASGITransport(app = app)

    async with AsyncClient(transport = transport, base_url = "https://test_rides") as ac:

        # Criação de corrida teste
        post_ride_response = await ac.post("/rides/", json={
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

        # Verifica se foi bem sucedida
        assert post_ride_response.status_code == 200

        # Faz a aquisição da corrida
        get_ride_response = await ac.get(f"/rides/{post_ride_response.json()["id"]}")

        # Verifica se foi bem sucedida
        assert get_ride_response.status_code == 200

        # Confirmação da correspondencia da corrida
        assert get_ride_response.json()["id"] == post_ride_response.json()["id"]