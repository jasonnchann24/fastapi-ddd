from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from fastapi_ddd.core.database import create_db_and_tables
from fastapi_ddd.core.api_router import api_router
from fastapi_ddd.core.database import engine
from fastapi_pagination import add_pagination
from fastapi.security import OAuth2PasswordBearer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    await create_db_and_tables()
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
add_pagination(app)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Include API router with all domain routers
app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("fastapi_ddd.main:app", host="0.0.0.0", port=8000, reload=True)
