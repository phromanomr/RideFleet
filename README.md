# VrumVrum 🚗

Serviço de transporte por aplicativo com federação distribuída.
Projeto da disciplina SIN 142 — Sistemas Distribuídos — UFV 2026/1.

## Pré-requisitos

- Docker Desktop

## Como rodar

```bash
python -m venv venv
```
```bash
venv\Scripts\activate  
```
```bash
docker compose up --build
```

A API estará disponível em `http://localhost` (porta 80, via Nginx).
Documentação interativa em `http://localhost/docs`.

> O Docker sobe automaticamente: banco de dados, duas instâncias da API e o load balancer Nginx. Não é necessário configurar nada manualmente.

---

## Endpoints disponíveis

### Corridas
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/rides/` | Solicitar uma corrida |
| GET | `/rides/{id}` | Consultar status de uma corrida |
| GET | `/audit/rides/{id}` | Log causal da corrida (Lamport) |

### Motoristas
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/drivers/` | Cadastrar motorista |
| GET | `/drivers/all` | Listar todos os motoristas |
| GET | `/drivers/stats` | Total e disponibilidade de motoristas |
| GET | `/drivers/{id}` | Consultar motorista |
| PATCH | `/drivers/{id}/availability` | Atualizar disponibilidade |
| DELETE | `/drivers/{id}` | Remover motorista |

### Sistema
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check do serviço |

---

## Arquitetura

```
Internet
    │
    ▼
 Nginx (porta 80)       ← load balancer (round-robin)
    │
    ├── api_1 (porta 8000)
    └── api_2 (porta 8000)

 PostgreSQL (porta 5432) ← persistência
 Loki (porta 3100)       ← coleta de logs
 Grafana (porta 3000)    ← visualização de logs
```

---

## Mecanismos de SD

Os mecanismos de sistemas distribuídos (travas, saga, consenso, circuit breaker e relógio lógico) são implementados e fornecidos pelo **Core** do RideFleet. O VrumVrum consome esses mecanismos via API padronizada — não os reimplementa.

| # | Requisito | Responsável |
|---|-----------|-------------|
| 1 | Travas Distribuídas | Core |
| 2 | Saga / Commit Distribuído | Core |
| 3 | Consenso / Leilão | Core |
| 4 | Circuit Breaker | Core |
| 5 | Relógio Lógico de Lamport | Core |

---

## Visualizar Logs

O VrumVrum envia logs estruturados em JSON para o **Grafana Loki**, visualizáveis via **Grafana**.

### URLs

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| Grafana | `http://localhost:3000` | admin / admin |
| Loki (API) | `http://localhost:3100` | — |

### Consultar logs no Grafana

1. Acessa `http://localhost:3000`
2. No menu lateral, clica em **Explore**
3. Seleciona o datasource **Loki**
4. Em **Label filters** seleciona `service` = `vrumvrum` e clica **Run query**

**Exemplos de queries LogQL:**

Todos os logs do serviço:
```
{service="vrumvrum"}
```

Filtrar por corrida (substitui pelo UUID retornado no POST /rides):
```
{service="vrumvrum"} | json | corrida_id="<uuid-da-corrida>"
```

Apenas erros:
```
{service="vrumvrum", level="error"}
```

Filtrar por tipo de evento:
```
{service="vrumvrum"} | json | event="ride_requested"
```

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOKI_URL` | — | URL do Loki (definida automaticamente pelo Docker) |

---

## Estrutura do projeto

```

app/
├── main.py                  — entrypoint da API
├── config.py                — constantes de configuração
├── state.py                 — estado em memória (fila, corridas)
├── database.py              — configuração do banco
├── logging_config.py        — configuração de logs estruturados (structlog)
├── logging_handlers.py      — handler HTTP para envio ao Loki
├── distributed/
│   └── logical_clock.py     — integração com o relógio de Lamport do Core
├── models/
│   ├── ride.py              — dataclass da corrida
│   ├── ride_model.py        — modelo SQLAlchemy da corrida
│   ├── driver.py            — dataclass do motorista
│   ├── driver_model.py      — modelo SQLAlchemy do motorista
│   ├── location.py          — modelo de endereço
│   └── schemas.py           — schemas Pydantic
├── routers/
│   ├── rides.py             — endpoints de corrida
│   ├── drivers.py           — endpoints de motorista
│   └── audit.py             — endpoints de auditoria
├── services/
│   ├── ride_service.py      — lógica de negócio das corridas
│   └── driver_service.py    — lógica de negócio dos motoristas
infra/
├── nginx/
│   └── nginx.conf           — configuração do load balancer
└── grafana/
    └── provisioning/
        └── datasources/
            └── loki.yml     — auto-provisioning do Loki como datasource
alembic/                     — migrations do banco
tests/                       — testes unitários
```

