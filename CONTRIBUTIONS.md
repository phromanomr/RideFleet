# Membros do Grupo

Phelipe Romano - 8135

André Paz Neiva - 8103

Sofia Castilho - 8145

Mariana Escorcer - 8115

# Contribuições

## André Paz Neiva (8103)
- Estrutura básica da API com FastAPI
- Modelo Ride com enum de status (REQUESTED, MATCH, CONFIRMED, IN_TRANSIT, COMPLETED, CANCELED)
- Schemas Pydantic (RideRequest e RideResponse)
- Routers para corridas:
  - `POST /rides/` - solicitar corrida
  - `GET /rides/{id}` - consultar status
- Router de auditoria:
  - `GET /audit/rides/{id}` - log causal com ordenação causal
- Relógio lógico de Lamport para auditoria distribuída
- Infraestrutura Docker (Dockerfile e docker-compose.yml com PostgreSQL e Redis)
- Modelo Location
- Configuração de dependências (requirements.txt com FastAPI, Uvicorn, Pydantic, etc.)
- Implementação do RideService para lógica de negócios
