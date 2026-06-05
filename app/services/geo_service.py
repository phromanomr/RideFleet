# app/services/geo_service.py

import httpx
from app.config import ORS_API_KEY, PRECO_BASE, PRECO_POR_KM
from app.logging_config import get_logger

logger = get_logger()

ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"


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
            response = await client.post(ORS_URL, json=payload, headers=headers)
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