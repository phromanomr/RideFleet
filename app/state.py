from collections import deque
from app.config import MAX_DRIVERS

# corridas indexadas por id
corridas: dict = {}

# fila de corridas aguardando motorista (deque mantém a ordem)
fila: deque = deque()

# quantos motoristas estão ocupados no momento
motoristas_ocupados: int = 0

# quantos motoristas temos no total
total_motoristas: int = MAX_DRIVERS