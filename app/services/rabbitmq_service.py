import json
import asyncio
import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractIncomingMessage
from app.config import RABBITMQ_URL
from app.logging_config import get_logger

logger = get_logger()

# Variáveis globais para manter a conexão
connection: AbstractRobustConnection | None = None
channel: aio_pika.abc.AbstractChannel | None = None

QUEUE_ENTRADA = "fila_entrada_corridas"
QUEUE_SAIDA = "fila_saida_corridas"

async def init_rabbitmq():
    """Inicialização do RabbitMQ"""
    global connection, channel
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        
        # Declarar AMBAS as filas
        await channel.declare_queue(QUEUE_ENTRADA, durable=True)
        await channel.declare_queue(QUEUE_SAIDA, durable=True) # Nova fila
        
        logger.info("rabbitmq_connected", url=RABBITMQ_URL)
    except Exception as e:
        logger.error("rabbitmq_connection_error", error=str(e))

async def publicar_corrida_saida(corrida_dict: dict):
    """Envia uma corrida para a fila de saída (aguardando delegação para o Core)."""
    if not channel:
        return
    mensagem = aio_pika.Message(
        body=json.dumps(corrida_dict).encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    )
    await channel.default_exchange.publish(
        mensagem,
        routing_key=QUEUE_SAIDA
    )
    logger.info("corrida_publicada_fila_saida_rabbitmq", corrida_id=corrida_dict.get("id"))

async def close_rabbitmq():
    """Fecha a conexão de forma limpa ao desligar a API."""
    global connection
    if connection:
        await connection.close()
        logger.info("rabbitmq_closed")

async def publicar_corrida_entrada(corrida_dict: dict):
    """Envia uma corrida serializada em JSON para a fila de entrada."""
    if not channel:
        return
    mensagem = aio_pika.Message(
        body=json.dumps(corrida_dict).encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    )
    await channel.default_exchange.publish(
        mensagem,
        routing_key=QUEUE_ENTRADA
    )
    logger.info("corrida_publicada_fila_rabbitmq", corrida_id=corrida_dict.get("id"))

async def consumir_fila_entrada(callback):
    """Fica escutando mensagens na fila e chama o callback de processamento."""
    # await asyncio.sleep(30) - para teste do log warning
    if not channel:
        return
    queue = await channel.declare_queue(QUEUE_ENTRADA, durable=True)
    
    async def process_message(message: AbstractIncomingMessage):
        # Transforma o JSON de volta em Dicionário
        corrida_dict = json.loads(message.body.decode())
        
        # A lógica de negócio ficará no callback. 
        # Ele deve retornar True (sucesso) ou False (falha, ex: sem motorista livre)
        sucesso = await callback(corrida_dict)
        
        if sucesso:
            await message.ack() # Confirma o processamento para retirar da fila
        else:
            await asyncio.sleep(2) # Pausa rápida para não fritar o processador em loop infinito
            await message.nack(requeue=True) # Devolve para o RabbitMQ tentar depois
            
    await queue.consume(process_message)
    logger.info("rabbitmq_consumer_started", queue=QUEUE_ENTRADA)

async def obter_tamanho_fila() -> int:
    """Útil para o endpoint de health check e para a política de overflow."""
    if not channel:
        return 0
    queue = await channel.declare_queue(QUEUE_ENTRADA, durable=True)
    return queue.declaration_result.message_count