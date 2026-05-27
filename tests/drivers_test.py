# Arquivo de testes do endpoint de drivers

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_driver():
    """Testa criação de motorista"""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="https://test_drivers") as ac:
        # Criar motorista
        response = await ac.post("/drivers/", json={
            "name": "João Silva",
            "license_plate": "ABC-1234"
        })

        assert response.status_code == 201
        driver = response.json()
        assert driver["name"] == "João Silva"
        assert driver["license_plate"] == "ABC-1234"
        assert "id" in driver
        assert "available" in driver


@pytest.mark.asyncio
async def test_get_driver_rides():
    """Testa endpoint GET /drivers/{driver_id}/rides"""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="https://test_drivers") as ac:
        # Criar motorista
        driver_response = await ac.post("/drivers/", json={
            "name": "Maria Santos",
            "license_plate": "XYZ-9876"
        })

        driver_id = driver_response.json()["id"]

        # Testar GET /drivers/{driver_id}/rides (sem vinculação de corridas ainda)
        rides_response = await ac.get(f"/drivers/{driver_id}/rides")
        assert rides_response.status_code == 200
        rides = rides_response.json()
        assert isinstance(rides, list)

        # Verificar estrutura de RideResponse se houver corridas
        for ride in rides:
            assert "id" in ride
            assert "status" in ride
            assert "passenger_id" in ride
            assert "driver_id" in ride
            assert "origin" in ride
            assert "destination" in ride
            assert "lamport_clock" in ride
            # Verificar que o driver_id está vinculado
            assert ride["driver_id"] == driver_id
            # Verificar estrutura de Location
            assert "lat" in ride["origin"]
            assert "lng" in ride["origin"]
            assert "city" in ride["origin"]
            assert "state" in ride["origin"]


@pytest.mark.asyncio
async def test_get_driver_rides_invalid_id():
    """Testa GET /drivers/{driver_id}/rides com ID inválido"""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="https://test_drivers") as ac:
        # Testar com ID inválido (deve retornar lista vazia)
        response = await ac.get("/drivers/invalid-driver-id/rides")
        assert response.status_code == 200
        rides = response.json()
        assert isinstance(rides, list)
        assert len(rides) == 0


@pytest.mark.asyncio
async def test_get_all_drivers():
    """Testa endpoint GET /drivers/all"""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="https://test_drivers") as ac:
        # Criar motorista
        await ac.post("/drivers/", json={
            "name": "Carlos Mendes",
            "license_plate": "DEF-5678"
        })

        # Teste GET /drivers/all
        response = await ac.get("/drivers/all")
        assert response.status_code == 200
        drivers = response.json()
        assert isinstance(drivers, list)
        assert len(drivers) >= 1

        # Verificar estrutura
        for driver in drivers:
            assert "id" in driver
            assert "name" in driver
            assert "license_plate" in driver
            assert "available" in driver


@pytest.mark.asyncio
async def test_get_driver_by_id():
    """Testa endpoint GET /drivers/{driver_id}"""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="https://test_drivers") as ac:
        # Criar motorista
        create_response = await ac.post("/drivers/", json={
            "name": "Lucas Oliveira",
            "license_plate": "GHI-1357"
        })

        driver_id = create_response.json()["id"]

        # Testar GET /drivers/{driver_id}
        response = await ac.get(f"/drivers/{driver_id}")
        assert response.status_code == 200
        driver = response.json()
        assert driver["id"] == driver_id
        assert driver["name"] == "Lucas Oliveira"
        assert driver["license_plate"] == "GHI-1357"

        # Testar com ID inválido
        invalid_response = await ac.get("/drivers/invalid-id")
        assert invalid_response.status_code == 404


@pytest.mark.asyncio
async def test_get_driver_stats():
    """Testa endpoint GET /drivers/stats"""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="https://test_drivers") as ac:
        # Criar alguns motoristas
        await ac.post("/drivers/", json={
            "name": "Pedro Costa",
            "license_plate": "JKL-2468"
        })

        # Testar GET /drivers/stats
        response = await ac.get("/drivers/stats")
        assert response.status_code == 200
        stats = response.json()
        assert "total" in stats
        assert "available" in stats
        assert "busy" in stats
        assert stats["total"] >= 1
        assert stats["available"] >= 0
        assert stats["busy"] >= 0

