# app/config.py

# --- Frota simulada ---
MAX_DRIVERS = 1          # total de motoristas disponíveis simultaneamente

# --- Fila de espera ---
MAX_QUEUE_SIZE = 3       # limite de corridas na fila antes de delegar ao Core # MAX_QUEUE_SIZE = 2 para teste do warning

# --- Delays de transição de estado (em segundos) ---
DELAY_MATCH_TO_CONFIRM = 10 # DELAY_MATCH_TO_CONFIRM = 60 para teste do warning
DELAY_CONFIRMED_TO_IN_TRANSIT = 20
DELAY_IN_TRANSIT_TO_COMPLETED = 30

# --- Integração com o Core ---
CORE_URL = "http://core:8080/api/v1"
ORIGIN_SERVICE_ID = "vrumvrum"
ORIGIN_API_KEY = ""
AUCTION_TIMEOUT_SECONDS = 10

RABBITMQ_URL = "amqp://myuser:mypassword@rabbitmq:5672/"