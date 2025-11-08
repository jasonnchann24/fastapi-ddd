# FastAPI - DDD
A FastAPI project template / mini-framework to achieve simple Domain-Driven Design (DDD) architecture. Provides more modular structure and better separation of concerns for building scalable and maintainable applications.

> Work in Progress ⚠️

# Setup project
1. `cp .env.example .env`
1. `uv sync`
1. `uv run cli auth-jwt-secret` 
1. `docker-compose up -d`
1. `uv run cli dev`

# Domains
1. Each domain should have its own folder under `domains/`
1. Register domain to `core/config.py` `INSTALLED_DOMAINS`

# Event Bus
1. All events should be registered to shared contract in `core/events/contracts.py`
1. Domain events should be defined in each domain's `events.py`
1. Event handlers should be defined in each domain's `event_handlers.py`

# Structure Guides
1. Shared kernel code goes in `src/fastapi_ddd/core/`