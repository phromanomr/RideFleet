# app/config.py
import os

# --- Frota simulada ---
MAX_DRIVERS = 1          # total de motoristas disponíveis simultaneamente

# --- Fila de espera ---
MAX_QUEUE_SIZE = 3       # limite de corridas na fila antes de delegar ao Core # MAX_QUEUE_SIZE = 2 para teste do warning

# --- Timeout mensagens fila ---
TTL_QUEUE = 300000

# --- Delays de transição de estado (em segundos) ---
DELAY_MATCH_TO_CONFIRM = 10 # DELAY_MATCH_TO_CONFIRM = 60 para teste do warning
DELAY_CONFIRMED_TO_IN_TRANSIT = 20
DELAY_IN_TRANSIT_TO_COMPLETED = 30

# --- Integração com o Core ---
# CORE_URL = "http://core:8080/api/v1"
CORE_URL = "http://192.168.3.14:8081/api/v1"
VRUMVRUM_URL = "http://192.168.3.146"
ORIGIN_SERVICE_ID = "vrumvrum"
ORIGIN_API_KEY = ""
AUCTION_TIMEOUT_SECONDS = 10

RABBITMQ_URL = "amqp://myuser:mypassword@rabbitmq:5672/"

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5439/vrumvrum_test"

# --- Geolocalização ---
ORS_API_KEY = os.getenv("ORS_API_KEY", "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjFmZGE4MzgwYmYxZTRhNTBiODgwNTQ0NzIzNzdiMmM3IiwiaCI6Im11cm11cjY0In0=")
PRECO_BASE = 5.00
PRECO_POR_KM = 2.00