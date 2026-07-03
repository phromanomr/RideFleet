from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models.schemas import RideRequest, RideResponse
from app.models.ride import Ride
from app.distributed.logical_clock import log_event
from app.services.ride_service import (
    solicitar_corrida,
    salvar_corrida,
    buscar_corrida,
    listar_corridas,
    listar_corridas_em_andamento,
    buscar_status_corrida,
    ride_to_response
)
import httpx
from app.config import CORE_URL
from app.services.core_service import HEADERS    
import json

router = APIRouter(prefix="/rides", tags=["rides"])


@router.post("/", response_model=RideResponse)
async def request_ride(body: RideRequest, db: AsyncSession = Depends(get_db)):
    corrida = Ride(
        origin=body.origin,
        destination=body.destination,
        passenger_id=body.passenger_id,
    )
    corrida.lamport_clock = await log_event(
        ride_id=corrida.id,
        event_type="ride_requested",
        details={"origin": body.origin.city, "destination": body.destination.city},
        db=db,
        estado_anterior=None,
        estado_novo="request"
    )

    await salvar_corrida(corrida, db)
    await solicitar_corrida(corrida)

    return corrida

@router.get("/all", response_model=List[RideResponse])
async def get_all_rides(
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    rides_db = await listar_corridas(db, status=status)
    return [ride_to_response(r) for r in rides_db]

@router.get("/ongoing", response_model=List[RideResponse])
async def get_ongoing_rides(db: AsyncSession = Depends(get_db)):
    rides_db = await listar_corridas_em_andamento(db)
    return [ride_to_response(r) for r in rides_db]

@router.get("/{ride_id}/status")
async def get_status(ride_id: str, db: AsyncSession = Depends(get_db)):
    status = await buscar_status_corrida(ride_id, db)
    if status is None:
        raise HTTPException(status_code=404, detail="Corrida não encontrada")
    return {"id": ride_id, "status": status}

@router.get("/{ride_id}", response_model=RideResponse)
async def get_ride(ride_id: str, db: AsyncSession = Depends(get_db)):
    corrida = await buscar_corrida(ride_id, db)
    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não encontrada")
    from app.logging_config import get_logger
    logger = get_logger()

    # Se a corrida foi delegada ou possui UUID do Core, atuamos como Proxy (BFF)
    if corrida.core_ride_uuid or corrida.status in ["delegated", "assigned", "REQUEST"]:
        alvo_uuid = corrida.core_ride_uuid
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:

                resposta = await client.get(f"{CORE_URL}/rides/{alvo_uuid}/audit", headers=HEADERS)
                
                if resposta.status_code == 200:
                    dados_audit = resposta.json()
                    eventos = dados_audit.get("events", [])
                    resposta_formatada = ride_to_response(corrida)
                    
                    # 1. Identificar o Vencedor do Leilão
                    for ev in eventos:
                        if ev.get("eventType") == "auction_closed":
                            payload = ev.get("payload", {})
                            vencedor = payload.get("winner") or ev.get("serviceId")
                            if vencedor and vencedor != "core":
                                resposta_formatada["delegation_winner"] = vencedor

                    # 2. Convertendo todos os eventos em uma string única (em minúsculas)
                    # para procurar a existência de qualquer estado, independentemente do campo (toState, newState, eventType)
                    texto_eventos = json.dumps(eventos).lower()

                
                    # 3. BUSCA HIERÁRQUICA: Começando dos terminais descendo até a confirmação
                    if any(t in texto_eventos for t in ["complete", "completed", "finish", "finished"]):
                        resposta_formatada["status"] = "COMPLETE"
                    elif any(t in texto_eventos for t in ["cancel", "canceled", "cancelled", "failed", "no_driver"]):
                        resposta_formatada["status"] = "CANCELED"
                    elif any(t in texto_eventos for t in ["in_transit", "intransit", "started", "em_corrida"]):
                        resposta_formatada["status"] = "IN_TRANSIT"
                    elif any(t in texto_eventos for t in ["confirm", "confirmed", "match", "matched", "assigned", "accepted"]):
                        resposta_formatada["status"] = "CONFIRM"
                    # Se não achou texto de transição, mas encontrou que o leilão já tem vencedor, força CONFIRM
                    elif resposta_formatada.get("delegation_winner") and resposta_formatada.get("status") == "REQUEST":
                        resposta_formatada["status"] = "CONFIRM"

                    return resposta_formatada
                else:
                    logger.warning(f"Core retornou status {resposta.status_code} ao buscar /audit para {alvo_uuid}")

        except Exception as e:
            pass

    return ride_to_response(corrida)

@router.get("/{ride_id}/delegation")
async def get_delegation_info(ride_id: str, db: AsyncSession = Depends(get_db)):
    corrida = await buscar_corrida(ride_id, db)
    if not corrida:
        raise HTTPException(status_code=404, detail="Corrida não encontrada")
    return {
        "id": ride_id,
        "core_ride_uuid": corrida.core_ride_uuid,
        "delegation_winner": corrida.delegation_winner,
    }