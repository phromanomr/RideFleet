import time
from enum import Enum

class CircuitOpenError(Exception):
    pass

class CircuitState(Enum):
    CLOSED = "closed"       # funcionando normalmente
    OPEN = "open"           # bloqueado após falhas
    HALF_OPEN = "half_open" # testando se o serviço voltou

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at: float | None = None

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.opened_at = None

    def _on_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.time()


    def _should_attempt_reset(self) -> bool:
        if self.opened_at is None:
            return False
        expected_time = time.time() - self.opened_at
        return expected_time >= self.recovery_timeout

    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError(
                    f"Circuito aberto. Tentativas bloqueadas por "
                    f"{self.recovery_timeout}s após {self.failure_count} falhas."
                )
            
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return  result
        except Exception as e:
            self._on_failure()
            raise e