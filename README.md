# 🚗 RideFleet — API Distribuída de Gestão de Corridas

O **RideFleet** é um serviço distribuído de despacho e gerenciamento de corridas urbanas e frotas, construído com foco em **alta disponibilidade**, **observabilidade**, **mensageria assíncrona** e **federação entre nós autônomos**. O sistema opera com múltiplas instâncias balanceadas e integradas a um ecossistema central (*Core*), garantindo ordenação temporal de eventos e tolerância a falhas.

---

## 🏗️ Arquitetura e Funcionalidades

- **API RESTful (FastAPI & Pydantic):** Endpoints completos para gestão de ciclo de vida de corridas (`/rides`), cadastro e triagem espacial de motoristas (`/drivers`, `/geo`) e trilha de auditoria (`/audit`).
- **Mensageria Assíncrona (RabbitMQ):** Desacoplamento da ingestão de requisições e processamento em *background* via filas duráveis (`fila_entrada_corridas` e `fila_saida_corridas`), com controle de concorrência (*prefetch*) e TTL.
- **Consistência Distribuída e Federação:**
  - Implementação de **Relógio Lógico (*Logical Clock*)** para ordenação causal de eventos entre instâncias independentes.
  - Integração contínua com a API do **Core RideFleet** para delegação de corridas (*overflow*), participação em leilões e renovação automática de travas distribuídas (*Distributed Locks*).
- **Observabilidade Completa:**
  - **Métricas (Prometheus):** Coleta em tempo real de latência HTTP, transições de estado, travas e volume de corridas locais e delegadas.
  - **Logs Assíncronos (Grafana Loki):** Logging estruturado em formato JSON via *background worker* com rastreabilidade por requisição (`X-Request-ID`).
  - **Dashboards (Grafana):** Provisionamento automatizado dos dashboards *VrumVrum* (negócio) e *Observabilidade* (infraestrutura).
- **Balanceamento de Carga e Escala:** Múltiplas instâncias da API (`api_1` e `api_2`) orquestradas em rede e balanceadas via **Nginx**.
- **Persistência Relacional:** Banco de dados **PostgreSQL** com controle de versionamento de esquema via **Alembic**.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.12+
- **Framework Web:** FastAPI / Uvicorn
- **ORM & Migrações:** SQLAlchemy (Async/Sync) & Alembic
- **Mensageria:** RabbitMQ (`aio-pika`)
- **Observabilidade:** Prometheus, Grafana, Loki & Structlog
- **Infraestrutura & Proxy:** Docker, Docker Compose & Nginx
- **CI/CD:** GitHub Actions

---

## 🚀 Como Executar o Projeto

A execução de todo o ecossistema (APIs, Banco de Dados, Mensageria e Observabilidade) é gerenciada de forma centralizada via **Docker Compose**.

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e Docker Compose instalados.
- Python 3.12+ instalado localmente (para dependências e testes).

### Passo a Passo

#### 1. Clone o repositório

```bash
git clone https://github.com/phromanomr/ridefleet.git
```

#### 2. Acesse a pasta do projeto

```bash
cd ridefleet
```

#### 3. Instale as dependências locais

```bash
pip install -r requirements.txt
```

#### 4. Construa as imagens dos contêineres

```bash
docker-compose build
```

#### 5. Suba a infraestrutura em segundo plano

```bash
docker-compose up -d
```

Este comando iniciará:

- PostgreSQL
- RabbitMQ
- Prometheus
- Loki
- Grafana
- Instâncias da API (`api_1` e `api_2`)
- Proxy Nginx

#### 6. Verifique o status dos serviços

```bash
docker-compose ps
```

---

## 🌐 Endpoints e Portas Acessíveis

| Serviço | URL | Descrição |
|----------|------|------------|
| API Principal (via Nginx) | `http://localhost:80` | Gateway de entrada balanceado para a API REST |
| Swagger/OpenAPI | `http://localhost/docs` | Interface para testes de requisições |
| RabbitMQ Management | `http://localhost:15672` | Gestão de filas (*guest / guest*) |
| Grafana | `http://localhost:3000` | Dashboards de telemetria e logs (*admin / admin*) |
| Métricas Prometheus (API 1) | `http://localhost:8001/metrics` | Exportação de métricas da Instância 1 |

---

## 🧪 Executando Testes Automatizados

O projeto possui uma suíte de testes unitários, de integração, validação de auditoria e verificação do relógio lógico.

### Executar localmente

```bash
pytest -v
```

### Executar dentro de um contêiner ativo

```bash
docker-compose exec api_1 pytest -v
```

---

## 🔄 Automação e CI/CD

O pipeline automatizado via **GitHub Actions** (`.github/workflows/workflow.yaml`) garante qualidade e entrega contínua do código.

### Integração Contínua (CI)

A cada **Push** ou **Pull Request**, o pipeline:

- Provisiona o ambiente de testes;
- Instala dependências;
- Valida a integridade do projeto;
- Executa a suíte completa de testes;
- Realiza verificações automatizadas de qualidade.

### Entrega Contínua (CD)

Após aprovação e integração na branch principal:

- A imagem Docker é construída;
- A imagem é enviada para o registro configurado;
- O ambiente remoto é atualizado automaticamente via conexão segura (SSH).

---

## 📊 Principais Características

✅ Arquitetura distribuída e escalável  
✅ Balanceamento de carga com Nginx  
✅ Comunicação assíncrona com RabbitMQ  
✅ Ordenação causal com Relógio Lógico  
✅ Integração federada com Core RideFleet  
✅ Observabilidade completa com Prometheus, Loki e Grafana  
✅ Persistência relacional com PostgreSQL  
✅ Migrações automatizadas com Alembic  
✅ Pipeline CI/CD com GitHub Actions  
✅ Ambiente totalmente containerizado com Docker Compose
