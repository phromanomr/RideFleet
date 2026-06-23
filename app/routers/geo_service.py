from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import requests

from app.services.geo_service import buscar_coordenadas
from app.models.location import GeoLocation, Address

router = APIRouter(prefix="/geo", tags=["geolocation"])

class Point(BaseModel):
    # Coordenadas geográficas de um ponto
    lat: float
    lng: float


class RouteRequest(BaseModel):
    # Ponto de origem da rota
    origin: Point

    # Ponto de destino da rota
    destination: Point

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjFmZGE4MzgwYmYxZTRhNTBiODgwNTQ0NzIzNzdiMmM3IiwiaCI6Im11cm11cjY0In0="

@router.post("/coordenadas", response_model=GeoLocation)
async def obter_coordenadas(body: Address):
    """
    Converte um endereço em texto para coordenadas geográficas (Latitude e Longitude).
    """
    # Agora acessamos o endereço usando body.endereco
    coordenadas = await buscar_coordenadas(body.endereco)
    
    if not coordenadas:
        # Se a API não achar o endereço ou der erro, retornamos 404
        raise HTTPException(
            status_code=404, 
            detail="Não foi possível encontrar as coordenadas para o endereço fornecido."
        )
        
    return coordenadas

@router.post("/rota")
async def obter_rota(body: RouteRequest):

    try:
        # Consulta a API OpenRouteService para obter a rota entre origem e destino
        response = requests.post(
            "https://api.openrouteservice.org/v2/directions/driving-car/geojson",
            headers={
                "Authorization": ORS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "coordinates": [
                    [body.origin.lng, body.origin.lat],
                    [body.destination.lng, body.destination.lat],
                ]
            },
            timeout=15,
        )

        # Gera exceção caso a API retorne erro
        response.raise_for_status()

    except requests.RequestException as e:
        # Retorna erro caso não seja possível obter a rota
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar OpenRouteService: {str(e)}"
        )

    # Converte a resposta da API para JSON
    data = response.json()

    # Extrai a lista de coordenadas da rota retornada
    coordinates = (
        data["features"][0]["geometry"]["coordinates"]
    )

    # Obtém resumo da rota
    summary = data["features"][0]["properties"]["summary"]

    distancia_km = round(summary["distance"] / 1000, 2)
    duracao_s = int(summary["duration"])

    return {
        "coordinates": [
            {
                "lat": coord[1],
                "lng": coord[0]
            }
            for coord in coordinates
        ],
        "distancia_km": distancia_km,
        "duracao_s": duracao_s
    }