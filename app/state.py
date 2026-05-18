from collections import deque
from app.config import MAX_DRIVERS

# corridas indexadas por id
corridas: dict = {}

# fila de corridas aguardando motorista (deque mantém a ordem)
fila: deque = deque()
