# VrumVrum 🚗

Serviço de transporte por aplicativo com federação distribuída.
Projeto da disciplina SIN 142 — Sistemas Distribuídos — UFV 2026/1.

## Pré-requisitos

- Python 3.12+
- Docker Desktop

## Como rodar

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd RideFleet
```

### 2. Crie o ambiente virtual

```bash
python -m venv venv
```

**Windows:**
```bash
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Suba o banco e o Redis

```bash
docker compose up db -d
```

### 5. Rode a API

```bash
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000`.
Documentação interativa em `http://localhost:8000/docs`.

## Endpoints disponíveis

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check do serviço |
| POST | `/rides/` | Solicitar uma corrida |
| GET | `/rides/{id}` | Consultar status de uma corrida |
| GET | `/audit/rides/{id}` | Log causal da corrida (Lamport) |

## Mecanismos de SD implementados

| # | Requisito | Status |
|---|-----------|--------|
| 1 | Travas Distribuídas | 🚧 em desenvolvimento |
| 2 | Saga / Commit Distribuído | 🚧 em desenvolvimento |
| 3 | Consenso / Leilão | 🚧 em desenvolvimento |
| 4 | Circuit Breaker | 🚧 em desenvolvimento |
| 5 | Relógio Lógico de Lamport | ✅ implementado |

## Estrutura do projeto

```
app/
├── main.py              — entrypoint da API
├── distributed/         — mecanismos de SD
│   └── logical_clock.py — Req 5: Lamport
├── models/
│   ├── ride.py          — modelo da corrida
│   └── schemas.py       — schemas Pydantic
├── routers/
│   ├── rides.py         — endpoints de corrida
│   └── audit.py         — endpoints de auditoria
frontend/                — interface do usuário
infra/                   — configurações de infraestrutura
tests/                   — testes unitários
```