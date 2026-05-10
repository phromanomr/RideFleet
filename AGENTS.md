# RideFleet AI Agent Guidelines

## Architecture Overview
RideFleet is a distributed ride-sharing service built with FastAPI, implementing distributed systems concepts like Lamport logical clocks. The app uses PostgreSQL for data persistence and Redis for caching/distributed operations. Currently, only the Lamport clock is fully implemented; other mechanisms (saga, auction, circuit breaker, distributed locks) are placeholders in `app/distributed/`.

Key components:
- **Models**: `app/models/ride.py` defines the Ride class with status enum and Lamport clock integration.
- **Routers**: `app/routers/rides.py` handles ride requests/responses; `app/routers/audit.py` provides causal logs.
- **Distributed**: `app/distributed/logical_clock.py` implements Lamport clock with async locking and audit logging.

Data flows: Rides start as REQUESTED, use in-memory dict (temporary), and log events with Lamport timestamps. Federation is planned via `delegated_to` field.

## Developer Workflows
- **Run locally**: `uvicorn app.main:app --reload` after `docker compose up db redis -d`.
- **API docs**: Available at `http://localhost:8000/docs` (Swagger UI).
- **Health check**: GET `/health` returns service status.
- **Debugging**: Use `app/distributed/logical_clock.py` for event tracing; audit logs sorted by Lamport clock.

## Project Conventions
- **Naming**: Use Portuguese for domain terms (e.g., `corrida` for ride, `valor` for value) in variables and comments.
- **Async patterns**: All distributed operations use `asyncio.Lock` (see `LamportClock.tick()`).
- **Schemas**: Pydantic models in `app/models/schemas.py` for requests/responses; include `lamport_clock` in responses.
- **Event logging**: Use `log_event()` from `logical_clock.py` for auditable actions, passing `ride_id`, `event_type`, and `details` dict.
- **Global state**: Singletons like `lamport` clock instance; avoid for new features.
- **Imports**: Relative imports within `app/` (e.g., `from app.models.ride import Ride`).

## Integration Points
- **Database**: Async PostgreSQL via `asyncpg` (env: `DATABASE_URL`); not yet integrated, replace in-memory dict in `rides.py`.
- **Redis**: For distributed ops (env: `REDIS_URL`); use for locks/caching in future implementations.
- **Federation**: Planned cross-service communication; `delegated_to` in Ride model indicates delegation.
- **External deps**: Minimal; add to `requirements.txt` and Dockerfile for new libs.

When adding distributed features, extend `app/distributed/` with async implementations, following the Lamport pattern of locked state updates and event logging.</content>
<parameter name="filePath">C:\Users\andre\PycharmProjects\RideFleet\AGENTS.md
