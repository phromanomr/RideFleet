from fastapi import APIRouter, Response, Depends

from app.database import get_db
from app.models.core_schemas import RideAuctionNotification, ProposalResponse, RideAssignment

from app.models.location import Location
from app.models.ride import Ride, RideStatus
from app.services.ride_service import tem_motorista_disponivel, salvar_corrida, receber_corrida_delegada

from app.services.core_service import atualizar_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.distributed.logical_clock import lamport
from app.logging_config import get_logger



logger = get_logger()

router = APIRouter(tags=["Webhooks do Core"])

@router.post("/rides/incoming", response_model=ProposalResponse)
async def receber_notificacao_leilao(notificacao: RideAuctionNotification):
    """Recebimento de proposta (enviar aceitamento ou não aceitamento da corrida)"""

    relogio_sincronizado = await lamport.receive(notificacao.logicalTimestamp)

    tem_motorista = await tem_motorista_disponivel()

    if not tem_motorista:
        logger.info("leilao_recusado_sem_motoristas", ride_uuid=notificacao.rideUuid)
        return Response(status_code=204)

    # Calcula rota real via OpenRouteService
    rota = await calcular_rota(notificacao.origin, notificacao.destination)

    if rota is None:
        # Fallback: se a geo falhar, usa valores padrão
        logger.warning("geo_falhou_usando_fallback", ride_uuid=notificacao.rideUuid)
        eta = 120
        preco = 20.00
    else:
        eta = rota["duracao_s"]
        preco = calcular_preco(rota["distancia_km"])

    logger.info("proposta_enviada_leilao",
                ride_uuid=notificacao.rideUuid,
                eta=eta,
                preco=preco)

    return ProposalResponse(
        estimatedEta=eta,
        estimatedPrice=preco,
        logicalTimestamp=relogio_sincronizado
    )

@router.post("/rides/{ride_uuid}/assigned")
async def receber_atribuicao(
    ride_uuid: str,
    atribuicao: RideAssignment,
    db: AsyncSession = Depends(get_db)
):
    relogio_sincronizado = await lamport.receive(atribuicao.logicalTimestamp)

    try:
        await receber_corrida_delegada(
            ride_uuid=ride_uuid,
            origin=atribuicao.origin,
            destination=atribuicao.destination,
            passenger_id=atribuicao.passengerId,
            origin_service_id=atribuicao.originServiceId,
            lamport_clock=relogio_sincronizado,
            db=db,
        )
        await atualizar_status(ride_uuid, "confirm", relogio_sincronizado)
        logger.info("corrida_recebida_e_confirmada", ride_uuid=ride_uuid)
        return {"status": "accepted"}

    except Exception as e:
        logger.error("erro_ao_confirmar_atribuicao", ride_uuid=ride_uuid, erro=str(e))
        return Response(status_code=500)