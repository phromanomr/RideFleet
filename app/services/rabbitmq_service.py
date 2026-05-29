import json
import asyncio
import aio_pika
import httpx
from aio_pika.abc import AbstractRobustConnection, AbstractIncomingMessage
from app.config import RABBITMQ_URL, TTL_QUEUE
from app.logging_config import get_logger

logger = get_logger()

# Variáveis globais para manter a conexão
connection: AbstractRobustConnection | None = None
channel: aio_pika.abc.AbstractChannel | None = None

# Guarda referência às filas já declaradas para reutilizar
_queues: dict = {}

QUEUE_ENTRADA = "fila_entrada_corridas"
QUEUE_SAIDA = "fila_saida_corridas"


async def init_rabbitmq():
    """Inicialização do RabbitMQ: cria conexão, channel e declara as filas."""
    global connection, channel, _queues
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # Declara as filas e salva referência em _queues.
        # Isso evita re-declarações posteriores no mesmo channel,
        # o que causaria conflito quando o consumer já estiver ativo.
        _queues[QUEUE_ENTRADA] = await channel.declare_queue(
            QUEUE_ENTRADA, 
            durable=True,
            arguments={
                "x-message-ttl": TTL_QUEUE
            }
        )
        _queues[QUEUE_SAIDA] = await channel.declare_queue(
            QUEUE_SAIDA, 
            durable=True,
            arguments={
                "x-message-ttl": TTL_QUEUE
            }
        )

        logger.info("rabbitmq_connected", url=RABBITMQ_URL)
    except Exception as e:
        logger.error("rabbitmq_connection_error", error=str(e))


async def publicar_corrida_saida(corrida_dict: dict):
    """Envia uma corrida para a fila de saída (aguardando delegação para o Core)."""
    if not channel:
        return
    mensagem = aio_pika.Message(
        body=json.dumps(corrida_dict).encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await channel.default_exchange.publish(mensagem, routing_key=QUEUE_SAIDA)
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
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await channel.default_exchange.publish(mensagem, routing_key=QUEUE_ENTRADA)
    logger.info("corrida_publicada_fila_rabbitmq", corrida_id=corrida_dict.get("id"))


async def consumir_fila_entrada(callback):
    """Fica escutando mensagens na fila e chama o callback de processamento."""
    if not channel:
        return
    # Reutiliza a referência salva no init para não re-declarar no mesmo channel.
    # Fallback: declara caso init_rabbitmq não tenha sido chamado antes.
    queue = _queues.get(QUEUE_ENTRADA)
    if not queue:
        queue = await channel.declare_queue(QUEUE_ENTRADA, durable=True)
        _queues[QUEUE_ENTRADA] = queue

    async def process_message(message: AbstractIncomingMessage):
        corrida_dict = json.loads(message.body.decode())
        sucesso = await callback(corrida_dict)
        if sucesso:
            await message.ack()
        else:
            await asyncio.sleep(2)
            await message.nack(requeue=True)

    await queue.consume(process_message)
    logger.info("rabbitmq_consumer_started", queue=QUEUE_ENTRADA)


async def obter_tamanho_fila() -> int:
    """Pega o tamanho TOTAL da fila consultando a API REST do RabbitMQ."""
    # A URL usa a porta 15672 (Painel) e o vhost padrão '/' (codificado como %2F)
    api_url = "http://rabbitmq:15672/api/queues/%2F/fila_entrada_corridas"
    
    try:
        async with httpx.AsyncClient() as client:
            # Usando as credenciais definidas no seu docker-compose.yml
            response = await client.get(api_url, auth=("myuser", "mypassword"))
            
            if response.status_code == 200:
                data = response.json()
                # A chave "messages" contém a soma de Ready + Unacked
                total_mensagens = data.get("messages", 0)
                return total_mensagens
                
    except Exception as e:
        logger.error("erro_ao_consultar_api_rabbitmq", error=str(e))
        
    # Fallback de segurança: se a requisição HTTP falhar, usa o método antigo
    if channel:
        queue = await channel.declare_queue(QUEUE_ENTRADA, durable=True)
        return queue.declaration_result.message_count
    
    return 0

async def consumir_fila_saida(callback):
    """Fica escutando mensagens na fila de saída e delega ao Core."""
    if not channel:
        return
    queue = _queues.get(QUEUE_SAIDA)
    if not queue:
        queue = await channel.declare_queue(QUEUE_SAIDA, durable=True)
        _queues[QUEUE_SAIDA] = queue

    async def process_message(message: AbstractIncomingMessage):
        corrida_dict = json.loads(message.body.decode())
        sucesso = await callback(corrida_dict)
        if sucesso:
            await message.ack()
        else:
            await asyncio.sleep(2)
            await message.nack(requeue=True)

    await queue.consume(process_message)
    logger.info("rabbitmq_consumer_started", queue=QUEUE_SAIDA)
