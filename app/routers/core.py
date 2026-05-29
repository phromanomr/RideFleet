from fastapi import APIRouter, Response, Depends
from app.models.core_schemas import RideAuctionNotification, ProposalResponse, RideAssignment
from app.services.ride_service import tem_motorista_disponivel
from app.services.core_service import atualizar_status

from app.distributed.logical_clock import lamport
from app.logging_config import get_logger

logger = get_logger()

router = APIRouter(tags=["Webhooks do Core"])

@router.post("/rides/incoming", response_model=ProposalResponse)
async def receber_notificacao_leilao(notificacao: RideAuctionNotification):
    """Recebimento de proposta (enviar aceitamento ou não aceitamento da corrida)"""

    # Sincronizar o relógio
    relogio_sincronizado = await lamport.receive(notificacao.logicalTimestamp)
    
    tem_motorista = await tem_motorista_disponivel()
    
    if not tem_motorista:
        logger.info("leilao_recusado_sem_motoristas", ride_uuid=notificacao.rideUuid)
        return Response(status_code=204)
    
    logger.info("proposta_enviada_leilao", ride_uuid=notificacao.rideUuid)
        
    return ProposalResponse(
        estimatedEta=120,          
        estimatedPrice=20.00,      
        logicalTimestamp=relogio_sincronizado # Relógio matematicamente correto!
    )

@router.post("/rides/{ride_uuid}/assigned")
async def receber_atribuicao(ride_uuid: str, atribuicao: RideAssignment):
    """Confirmação de aceite, vitoria da corrida e recebimento do lock"""
    
    relogio_sincronizado = await lamport.receive(atribuicao.logicalTimestamp)
    
    try:
        # Enviar o status com o relógio atualizado
        await atualizar_status(ride_uuid, "confirm", relogio_sincronizado)
        logger.info("corrida_confirmada_com_sucesso", ride_uuid=ride_uuid)
        return {"status": "accepted"}
    except Exception as e:
        logger.error("erro_ao_confirmar_atribuicao", ride_uuid=ride_uuid, erro=str(e))
        return Response(status_code=500)