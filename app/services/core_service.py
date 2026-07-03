import httpx
from app.logging_config import get_logger
from app.config import (
    CORE_URL,
    ORIGIN_SERVICE_ID,
    ORIGIN_API_KEY
)

logger = get_logger()

HEADERS = {"X-API-Key": ORIGIN_API_KEY} 

async def solicitar_delegacao_core(corrida_dict: dict, lamport_clock: int):
    """Delega corrida ao core para leilão"""

    # Log
    logger.info("iniciando_delegacao_core", ride_uuid=corrida_dict.get("ride_uuid"))

    payload = {
        "originServiceId": ORIGIN_SERVICE_ID,
        "passengerId": corrida_dict["passenger_id"],
        "passengerName": "Tem que adicionar",
        "origin": corrida_dict["origin"],
        "destination": corrida_dict["destination"],
        "logicalTimestamp": lamport_clock,
        "auctionTimeoutSeconds": 10 # Tempo que o core vai esperar até definir um vencedor do leilão
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(f"{CORE_URL}/rides", json=payload, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        logger.info("resposta_bruta_delegacao_core", body=data)  # NOVO: log defensivo
        return data

async def atualizar_status(ride_uuid: str, novo_status: str, lamport_clock: int):
    """Atualiza o status de uma corrida"""

    # Log
    logger.info("atualizando_status", ride_uuid=ride_uuid, novo_status=novo_status)

    payload = {
        "newState": novo_status,
        "serviceId": ORIGIN_SERVICE_ID,
        "logicalTimestamp": lamport_clock
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.patch(f"{CORE_URL}/rides/{ride_uuid}/status", json=payload, headers=HEADERS)

        if response.status_code != 200:
            # Log
            logger.error("Erro ao atualizar status no Core", extra={"response": response.text})
        if response.status_code == 200:
            # Log
            logger.info("status_atualizado_com_sucesso", ride_uuid=ride_uuid, novo_status=novo_status)

        return response.json()

async def obter_log_causal(ride_uuid: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{CORE_URL}/rides/{ride_uuid}/audit", headers=HEADERS)
        return response.json()
 
async def renovar_lock(ride_uuid: str, ttl_seconds: int = 60) -> bool:
    """Renova o prazo do lock distribuído da corrida no Core. Chamar periodicamente em caso de demora para não perder o lock"""
    # O payload exige o serviceId e aceita um ttlSeconds (máximo 300)
    payload = {
        "serviceId": ORIGIN_SERVICE_ID,
        "ttlSeconds": ttl_seconds
    }
    
    url = f"{CORE_URL}/locks/{ride_uuid}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=HEADERS)
            
            if response.status_code == 200:
                dados = response.json()
                # Log
                logger.info("lock_renovado_com_sucesso", ride_uuid=ride_uuid, novo_vencimento=dados.get("expiresAt"))
                return True
                
            elif response.status_code == 409:
                # 409 significa que outro grupo detém o lock ativo no momento
                dados_conflito = response.json()
                # Log
                logger.warning("falha_renovacao_lock_perdido", ride_uuid=ride_uuid, detentorado_por=dados_conflito.get("heldBy"))
                return False
                
            else:
                # Log
                logger.error("erro_inesperado_ao_renovar_lock", ride_uuid=ride_uuid, status_code=response.status_code, body=response.text)
                return False
                
    except httpx.RequestError as e:
        # Log
        logger.error("erro_de_rede_ao_comunicar_com_core", erro=str(e))
        return False

async def obter_propostas_leilao(ride_uuid: str) -> dict | None:
    """Consulta o resultado do leilão (propostas) no Core"""

    url = f"{CORE_URL}/rides/{ride_uuid}/proposals"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=HEADERS)
            
            if response.status_code == 200:
                # Log
                logger.warning("propostas_obtidas", ride_uuid=ride_uuid, status_code=response.status_code, body=response.text)
                # Retorna o JSON com o vencedor e a lista de propostas
                return response.json()
                
            elif response.status_code == 404:
                # Log
                logger.warning("corrida_nao_encontrada_no_core", ride_uuid=ride_uuid)
                return None
                
            else:
                # Log
                logger.error("erro_ao_buscar_propostas",  ride_uuid=ride_uuid, status_code=response.status_code, body=response.text)
                return None
                
    except httpx.RequestError as e:
        # Log
        logger.error("erro_de_rede_ao_buscar_propostas", erro=str(e))
        return None