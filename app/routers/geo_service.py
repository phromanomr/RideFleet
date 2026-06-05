from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.geo_service import buscar_coordenadas
from app.models.location import GeoLocation, Address

router = APIRouter(prefix="/geo", tags=["geolocation"])

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