# app/services/geo_service.py

import httpx
import asyncio
from app.config import ORS_API_KEY, PRECO_BASE, PRECO_POR_KM
from app.logging_config import get_logger

logger = get_logger()

ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
ORS_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"


async def calcular_rota(origin: dict, destination: dict) -> dict | None:
    """
    Calcula distância e duração entre dois pontos via OpenRouteService.
    Retorna dict com distância em km e duração em segundos, ou None em caso de erro.
    """
    payload = {
        "coordinates": [
            [origin["lng"], origin["lat"]],
            [destination["lng"], destination["lat"]]
        ]
    }

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(ORS_GEOCODE_URL, json=payload, headers=headers)
            print(f"DEBUG RESPONSE: {response.text}") # Veja o que a API realmente responde
            response.raise_for_status()
            data = response.json()

            segmento = data["routes"][0]["summary"]
            distancia_km = segmento["distance"] / 1000
            duracao_s = int(segmento["duration"])

            logger.info("rota_calculada",
                        distancia_km=round(distancia_km, 2),
                        duracao_s=duracao_s)

            return {
                "distancia_km": distancia_km,
                "duracao_s": duracao_s
            }

    except Exception as e:
        logger.error("erro_ao_calcular_rota", erro=str(e))
        return None


def calcular_preco(distancia_km: float) -> float:
    """Calcula o preço da corrida com base na distância."""
    return round(PRECO_BASE + PRECO_POR_KM * distancia_km, 2)

async def buscar_coordenadas(endereco_completo: str) -> dict | None:
    """
    Busca a latitude e longitude de um endereço via OpenRouteService.
    """
    params = {
        "api_key": ORS_API_KEY,
        "text": endereco_completo,
        "size": 1  # Retorna apenas o resultado mais relevante
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(ORS_GEOCODE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("features") and len(data["features"]) > 0:
                # O OpenRouteService retorna um array com [longitude, latitude]
                lng, lat = data["features"][0]["geometry"]["coordinates"]
                return {"lat": lat, "lng": lng}
            
            logger.warning("endereco_nao_encontrado", endereco=endereco_completo)
            return None

    except Exception as e:
        logger.error("erro_ao_geocodificar", erro=str(e), endereco=endereco_completo)
        return None