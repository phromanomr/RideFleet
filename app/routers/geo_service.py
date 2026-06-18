from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import requests
import httpx

from app.services.geo_service import buscar_coordenadas, estimar_corrida
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
    coordenadas = await buscar_coordenadas(body.endereco)
    
    if not coordenadas:
        raise HTTPException(
            status_code=404, 
            detail="Não foi possível encontrar as coordenadas para o endereço fornecido."
        )
        
    return coordenadas

@router.post("/rota")
async def obter_rota(body: RouteRequest):
    # 1. Proteção: Verifica se origem e destino são iguais
    if body.origin.lat == body.destination.lat and body.origin.lng == body.destination.lng:
        raise HTTPException(
            status_code=400,
            detail="A origem e o destino não podem ser iguais."
        )

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
        # Pega a mensagem de erro original da API para facilitar o debug no console
        detalhes_erro = ""
        if hasattr(e, 'response') and e.response is not None:
            detalhes_erro = f" | Detalhes: {e.response.text}"

        # 2. Mudança: Retorna erro 400 em vez de 500 para não degradar o Health Check
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao consultar OpenRouteService: {str(e)}{detalhes_erro}"
        )

    # Converte a resposta da API para JSON
    data = response.json()

    # Verifica se a estrutura esperada realmente existe na resposta
    if "features" not in data or not data["features"]:
        raise HTTPException(
            status_code=400,
            detail="A API de rotas não retornou caminhos válidos para estas coordenadas."
        )

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

@router.post("/estimate")
async def estimate_route(body: dict):
    return await estimar_corrida(
        body["origin"],
        body["destination"]
    )

@router.get("/search")
async def buscar_endereco(q: str):
    headers = {"User-Agent": "VrumVrum-App/1.0 (contato@seuemail.com)"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"format": "json", "addressdetails": 1, "q": q, "limit": 5},
            headers=headers,
        )
        return resp.json()