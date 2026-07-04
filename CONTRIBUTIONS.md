# Membros do Grupo

André Paz Neiva - 8103

Mariana Escorcer - 8115

Phelipe Romano - 8135

Sofia Castilho - 8145

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

## Phelipe Romano (8135)
### Arquitetura da Aplicação e Persistência de Dados
- Estruturação dos modelos de domínio ORM (`app/models/`) para motoristas, corridas, geolocalização e eventos de auditoria
- Definição dos esquemas de serialização e validação de contratos de dados (DTOs) com Pydantic (`schemas.py` e `core_schemas.py`)
- Configuração e gerenciamento do pool de conexões com o banco de dados relacional (`database.py`)
- Estruturação do fluxo de controle de versão de schema do banco de dados com Alembic e redação dos scripts de migração iniciais

### Núcleo da API RESTful e Roteamento HTTP
- Configuração do ponto de entrada da API RESTful (`main.py`), injeção de middlewares globais e gerenciamento de estado da aplicação (`state.py`)
- Desenvolvimento de endpoints e controladores para o ciclo de vida de corridas (`rides.py`), gestão de motoristas (`drivers.py`) e serviços espaciais (`geo_service.py`)
- Exposição de rotas de monitoramento de saúde de contêineres (`health.py`) e consultas de histórico de eventos de auditoria (`audit.py`)

### Sistemas Distribuídos e Federação (Core RideFleet)
- Implementação do algoritmo de Relógio Lógico (*Logical Clock*) para sincronização de eventos em ambiente distribuído (`logical_clock.py`)
- Construção da camada de serviços federados (`core_service.py`) para comunicação com o Core, gestão de leilões e controle de travas distribuídas

### Mensageria e Processamento Assíncrono (RabbitMQ)
- Integração com broker de mensageria RabbitMQ via `aio-pika` para desacoplamento assíncrono e processamento de filas de alta demanda (`rabbitmq_service.py`)
- Implementação de consumidores assíncronos e produtores de mensagens integrados ao ciclo de vida da aplicação FastAPI

### Observabilidade, Logging e Telemetria
- Implementação de logging estruturado em formato JSON com envio assíncrono em background para o Grafana Loki
- Instrumentação de telemetria e monitoramento de desempenho e negócio com exportação de métricas via Prometheus (`metrics.py`)
- Provisionamento automatizado e estruturação de dashboards analíticos e operacionais no Grafana (`observabilidade.json` e `vrumvrum.json`)

### Qualidade de Software e Testes Automatizados
- Configuração do framework de testes Pytest, *fixtures* e clientes HTTP de teste (`pytest.ini` e `conftest.py`)
- Desenvolvimento de suíte de testes unitários, de integração (`rides_test.py`, `drivers_test.py`), de relógio lógico e de contratos da API

### CI/CD, Infraestrutura e DevOps
- Containerização da aplicação via `Dockerfile` multi-stage e automação de pré-requisitos de inicialização (`entrypoint.sh`)
- Orquestração de contêineres e balanceamento de tráfego entre instâncias distribuídas utilizando Docker Compose e Nginx
- Construção de pipelines automatizados de CI/CD via GitHub Actions para *linting*, execução de testes, build e deploy contínuo em servidor remoto

## Sofia Castilho (8145)
### Banco de Dados e Persistência
- Configuração da conexão assíncrona com PostgreSQL via SQLAlchemy 2.x (app/database.py)
- Implementação do modelo SQLAlchemy RideModel com achatamento dos campos de Location em colunas individuais (origin_*, destination_*)
- Implementação do modelo SQLAlchemy AuditModel para persistência do histórico de eventos de auditoria
- Substituição do armazenamento em memória (corridas = {}) por persistência real no PostgreSQL
- Funções de repositório: salvar_corrida(), buscar_corrida(), atualizar_corrida(), listar_corridas(), listar_corridas_em_andamento(), buscar_status_corrida()

### Migrations (Alembic)
- Configuração do Alembic com suporte a conexões assíncronas
- Migration inicial da tabela rides
- Migration da tabela drivers
- Migration da tabela audit_events com índice em ride_id
- Migration de correção do campo ride_id
- Integração das migrations ao entrypoint.sh para execução automática na inicialização do container

### Logging Estruturado
- Configuração do structlog para saída em JSON estruturado (app/logging_config.py)
- LOG_LEVEL configurável via variável de ambiente (padrão: INFO)
- Processor de exceções estruturadas (stack traces em JSON via format_exc_info)
- Captura dos logs internos do Uvicorn no mesmo formato JSON
- Implementação da função log_estruturado() com campos obrigatórios do Core: corrida_id, estado_anterior, estado_novo, lamport_clock
- Middleware de request_id automático para correlação de logs por requisição (app/main.py)
- Integração do log estruturado em todos os fluxos de negócio: criação de corrida, atribuição de motorista, enfileiramento e overflow

### Handler HTTP para Loki
- Implementação do LokiQueueHandler com envio assíncrono via fila em background (app/logging_handlers.py)
- Ativação automática quando a variável de ambiente LOKI_URL estiver definida

### Observabilidade — Infraestrutura de Logs
- Adição do Grafana Loki ao docker-compose.yml (porta 3109)
- Adição do Grafana ao docker-compose.yml (porta 3009)
- Auto-provisioning do Loki como datasource no Grafana via infra/grafana/provisioning/datasources/loki.yml

### Observabilidade — Métricas
- Implementação da métrica de estado do serviço (vrumvrum_servico_estado: 0=UP, 1=DEGRADED, 2=DOWN)
- Implementação da métrica de tamanho da fila de saída (vrumvrum_fila_saida_tamanho)
- Implementação da métrica de distribuição de carga entre instâncias (vrumvrum_requisicoes_por_instancia)
- Adição dos painéis correspondentes no dashboard Grafana

### Containerização
- Criação do entrypoint.sh com verificação de disponibilidade do banco, execução de migrations e inicialização da API
- Correção de incompatibilidade de line endings (CRLF/LF) para execução em containers Linux
- Exposição da porta 5432 do PostgreSQL para acesso externo pelo Alembic
- Atualização do docker-compose.yml para variáveis de ambiente, volumes e dependências

### Documentação
- Seção "Visualizar Logs" no README.md com URLs, queries LogQL e variáveis de ambiente
- Seção "Estrutura do projeto" atualizada com os novos arquivos
