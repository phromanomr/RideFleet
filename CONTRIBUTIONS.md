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

## Mariana Escorcer (8115)

### Monitoramento e Health Check
- Implementação do endpoint `GET /health`.
- Exposição do estado geral do serviço (`UP`, `DEGRADED` e `DOWN`).
- Inclusão de informações de monitoramento no health check:
  - quantidade de motoristas disponíveis;
  - tamanho da fila de corridas;
  - latência média recente.
- Integração do Health Check ao Docker Compose para monitoramento dos containers.

### Observabilidade
- Implementação do endpoint `/metrics` compatível com Prometheus.
- Desenvolvimento das métricas de:
  - corridas locais;
  - corridas delegadas para outros serviços;
  - corridas recebidas por delegação;
  - latência dos endpoints;
  - throughput de requisições.
- Configuração da infraestrutura de monitoramento com Prometheus.
- Configuração dos dashboards no Grafana para visualização das métricas.

### Geolocalização
- Implementação da integração com o serviço de geolocalização para cálculo de rotas.
- Desenvolvimento do cálculo de ETA para estimativa do tempo de chegada.
- Integração da geolocalização ao fluxo de solicitação e acompanhamento de corridas.

### Corridas
- Implementação da indicação do serviço/grupo responsável por corridas delegadas.
- Adequação dos modelos e respostas da API para suportar informações de delegação.

### Front-end *(repositório separado)*
- Desenvolvimento da tela de solicitação de corrida.
- Desenvolvimento da tela de acompanhamento da corrida.
- Integração do aplicativo com os endpoints do backend.
- Implementação da atualização do status da corrida em tempo real.
- Exibição do ETA da corrida.
- Implementação da indicação do serviço de origem em corridas delegadas.
- Implementação da visualização do motorista e da localização no mapa.
- Integração das funcionalidades de geolocalização com a interface do usuário.
