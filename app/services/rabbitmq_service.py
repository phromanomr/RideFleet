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
        _queues[QUEUE_ENTRADA] = await channel.declare_queue(QUEUE_ENTRADA, durable=True)
        _queues[QUEUE_SAIDA] = await channel.declare_queue(QUEUE_SAIDA, durable=True)

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
    """
    Retorna o número de mensagens pendentes na fila de entrada.

    Por que channel temporário com passive=True?
    O channel principal já tem um consumer ativo (consumir_fila_entrada).
    Re-declarar uma fila no mesmo channel que está sendo consumido causa
    conflito no aio_pika e pode lançar exceção ou retornar contagem errada.
    A solução é abrir um channel temporário só para inspecionar (passive=True
    garante que nenhuma fila é criada/alterada) e fechá-lo logo em seguida.
    """
    if not channel:
        return 0
    try:
        queue = _queues.get(QUEUE_ENTRADA)
        if queue:
            temp_channel = await connection.channel()
            try:
                # passive=True: só lê o estado da fila, sem criar nem modificar
                temp_queue = await temp_channel.declare_queue(
                    QUEUE_ENTRADA, durable=True, passive=True
                )
                return temp_queue.declaration_result.message_count
            finally:
                await temp_channel.close()
        return 0
    except Exception as e:
        logger.warning("obter_tamanho_fila_erro", error=str(e))
        return 0