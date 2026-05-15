import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_get_ride():

    transport = ASGITransport(app = app)

    async with AsyncClient(transport = transport, base_url = "https://test_get_ride") as ac:

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

        assert create_ride_response.status_code == 200

        response = await ac.get(f"audit/rides/{create_ride_response.json()["id"]}")

    assert response.status_code == 200
    assert response.json()["ride_id"] == create_ride_response.json()["id"]