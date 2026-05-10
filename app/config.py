# app/config.py

# --- Frota simulada ---
MAX_DRIVERS = 5          # total de motoristas disponíveis simultaneamente
REJECTION_CHANCE = 0.20  # 20% de chance de um motorista recusar a corrida

# --- Fila de espera ---
MAX_QUEUE_SIZE = 3       # limite de corridas na fila antes de delegar ao Core

# --- Delays de transição de estado (em segundos) ---
DELAY_MATCH_TO_CONFIRMED = 3
DELAY_CONFIRMED_TO_IN_TRANSIT = 5
DELAY_IN_TRANSIT_TO_COMPLETED = 10

# --- Integração com o Core ---
CORE_URL = "http://core:8080/api/v1"
ORIGIN_SERVICE_ID = "vrumvrum"
AUCTION_TIMEOUT_SECONDS = 10