from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from fastapi_ddd.core.database import create_db_and_tables
from fastapi_ddd.core.api_router import api_router
from fastapi_ddd.core.database import engine
from fastapi_pagination import add_pagination
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi_ddd.core.events.event_bus import SimpleEventBus
from fastapi_ddd.core.events.bootstrap import register_domain_event_handlers
from fastapi_ddd.core.containers import register_event_bus

# Initialize EventBus and register it in DI container BEFORE domain imports
event_bus = SimpleEventBus()
register_event_bus(event_bus)
register_domain_event_handlers(event_bus)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    await create_db_and_tables()
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:3000",  # React
#         "http://localhost:5173",  # Vite
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

add_pagination(app)

# Include API router with all domain routers
app.include_router(api_router)

# Store event bus in app state for potential direct access
app.state.event_bus = event_bus


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("fastapi_ddd.main:app", host="0.0.0.0", port=8000, reload=True)
