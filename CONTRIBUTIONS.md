# Membros do Grupo

Phelipe Romano - 8135

André Paz Neiva - 8103

Sofia Castilho - 8145

Mariana Escorcer - 8115

# Contribuições

## André Paz Neiva (8103)

### Estrutura base da API
- Estrutura inicial da API com FastAPI + Uvicorn
- Configuração de dependências (`requirements.txt`)
- Infraestrutura Docker (`Dockerfile` e `docker-compose.yml` com PostgreSQL)

### Modelos e Schemas
- Modelo `Location` com campos lat, lng, street, number, city, state
- Modelo `Ride` (dataclass) com enum `RideStatus` (REQUEST, MATCH, CONFIRM, IN_TRANSIT, COMPLETE, CANCELED)
- Modelo `Driver` (dataclass) com controle de disponibilidade
- Schemas Pydantic: `RideRequest`, `RideResponse`, `DriverRequest`, `DriverResponse`, `DriverStats`

### Endpoints de Corridas
- `POST /rides/` — solicitar corrida
- `GET /rides/{id}` — consultar corrida
- `GET /rides/ongoing` — listar corridas em andamento'
- `GET /rides/{ride_id}/status` — consultar status da corrida
- `GET /rides/all` — listar todas as corridas"

### Endpoints de Motoristas
- `POST /drivers/` — cadastrar motorista
- `GET /drivers/all` — listar todos os motoristas
- `GET /drivers/stats` — total e disponibilidade de motoristas
- `GET /drivers/{id}` — consultar motorista
- `PATCH /drivers/{id}/availability` — atualizar disponibilidade
- `DELETE /drivers/{id}` — remover motorista
- `GET /drivers/{driver_id}/rides` — listar corridas associadas a um motorista

### Endpoints de Auditoria
- `GET /audit/rides/{id}` — log causal com ordenação por relógio de Lamport

### Lógica de Negócio (RideService)
- Política de overflow: delega ao Core quando fila atinge `MAX_QUEUE_SIZE`
- Simulação de transições de estado em background (MATCH → CONFIRM → IN_TRANSIT → COMPLETE)
- Recebimento de corridas delegadas via Core (`receber_corrida_delegada`)

### Lógica de Negócio (DriverService)
- CRUD completo de motoristas com persistência no PostgreSQL
- Controle de disponibilidade integrado ao fluxo de corridas
- Contagem de motoristas disponíveis e ocupados

### Mecanismos de Sistemas Distribuídos
- Relógio lógico de Lamport: `tick()`, `receive()` e log de auditoria causal
- Integração do relógio com todos os eventos do serviço

### Infraestrutura
- Load balancer Nginx com duas instâncias da API (round-robin)

### Geolocalização
- `geo_service.py` — cálculo de ETA e preço via OpenRouteService
- Cálculo de preço: R$ 5,00 base + R$ 2,00/km
- Fallback automático para valores padrão em caso de falha da API

### Testes
- Testes de contrato para os webhooks de entrada do Core
- Mock de RabbitMQ, Core e geolocalização para testes isolados

### Documentação
- `README.md` com instruções de execução, arquitetura e endpoints