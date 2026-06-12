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
                "lat": -18.00, "lng": -17.89,
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


@pytest.mark.asyncio
async def test_get_ride_status():
    """Testa o endpoint GET /rides/{ride_id}/status"""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="https://test_rides") as ac:
        # Criar corrida
        post_response = await ac.post("/rides/", json={
            "passenger_id": "passageiro_status_test",
            "origin": {
                "lat": -18.00, "lng": -18.00,
                "street": "Rua teste", "number": "1",
                "city": "Rio Paranaíba", "state": "MG"
            },
            "destination": {
                "lat": -18.00, "lng": -17.89,
                "street": "Rua teste", "number": "2",
                "city": "Rio Paranaíba", "state": "MG"
            }
        })

        ride_id = post_response.json()["id"]

        # Testar GET /rides/{ride_id}/status
        status_response = await ac.get(f"/rides/{ride_id}/status")
        assert status_response.status_code == 200
        assert "status" in status_response.json()
        assert "id" in status_response.json()
        assert status_response.json()["id"] == ride_id

        # Testar com ID inválido
        invalid_response = await ac.get("/rides/invalid-id/status")
        assert invalid_response.status_code == 404


@pytest.mark.asyncio
async def test_get_all_rides():
    """Testa o endpoint GET /rides/all"""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="https://test_rides") as ac:
        # Criar duas corridas
        ride1 = await ac.post("/rides/", json={
            "passenger_id": "passageiro_all_1",
            "origin": {
                "lat": -18.00, "lng": -18.00,
                "street": "Rua teste", "number": "1",
                "city": "Rio Paranaíba", "state": "MG"
            },
            "destination": {
                "lat": -18.00, "lng": -17.89,
                "street": "Rua teste", "number": "2",
                "city": "Rio Paranaíba", "state": "MG"
            }
        })

        ride2 = await ac.post("/rides/", json={
            "passenger_id": "passageiro_all_2",
            "origin": {
                "lat": -18.00, "lng": -18.00,
                "street": "Rua teste", "number": "1",
                "city": "Rio Paranaíba", "state": "MG"
            },
            "destination": {
                "lat": -18.00, "lng": -17.89,
                "street": "Rua teste", "number": "2",
                "city": "Rio Paranaíba", "state": "MG"
            }
        })

        # Testar GET /rides/all
        all_response = await ac.get("/rides/all")
        assert all_response.status_code == 200
        rides = all_response.json()
        assert isinstance(rides, list)
        assert len(rides) >= 2

        # Verificar estrutura de RideResponse
        for ride in rides:
            assert "id" in ride
            assert "status" in ride
            assert "passenger_id" in ride
            assert "origin" in ride
            assert "destination" in ride
            assert "lamport_clock" in ride
            # Verificar estrutura de Location
            assert "lat" in ride["origin"]
            assert "lng" in ride["origin"]
            assert "city" in ride["origin"]
            assert "state" in ride["origin"]


@pytest.mark.asyncio
async def test_get_all_rides_with_status_filter():
    """Testa GET /rides/all com filtro de status"""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="https://test_rides") as ac:
        # Criar corrida
        post_response = await ac.post("/rides/", json={
            "passenger_id": "passageiro_filter_test",
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

        # Testar com filtro de status válido
        response = await ac.get("/rides/all?status=REQUEST")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

        # Testar com filtro de status inválido (deve retornar lista vazia)
        response = await ac.get("/rides/all?status=INVALID_STATUS")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_ongoing_rides():
    """Testa o endpoint GET /rides/ongoing"""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="https://test_rides") as ac:
        # Testar GET /rides/ongoing
        response = await ac.get("/rides/ongoing")
        assert response.status_code == 200
        rides = response.json()
        assert isinstance(rides, list)

        # Verificar estrutura de RideResponse
        for ride in rides:
            assert "id" in ride
            assert "status" in ride
            assert "passenger_id" in ride
            assert "origin" in ride
            assert "destination" in ride
            # Status deve estar em andamento (MATCH, CONFIRM, IN_TRANSIT)
            assert ride["status"] in ["MATCH", "CONFIRM", "IN_TRANSIT"]
