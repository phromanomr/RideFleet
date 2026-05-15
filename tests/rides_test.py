import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_rides():
    
    transport = ASGITransport(app = app)

    async with AsyncClient(transport = transport, base_url = "https://test_rides") as ac:

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

        assert post_ride_response.status_code == 200

        get_ride_response = await ac.get(f"/rides/{post_ride_response.json()["id"]}")

        assert get_ride_response.status_code == 200
        assert get_ride_response.json()["id"] == post_ride_response.json()["id"]