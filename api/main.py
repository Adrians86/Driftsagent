from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import create_db_and_tables
from api.routers import firma, lager, service
from api.routers.driftsagent_router import router as driftsagent_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Driftsagent API",
    description="AI agent platform for Norwegian SMBs — logistics, procurement, service and production.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(firma.router)
app.include_router(lager.router)
app.include_router(service.router)
app.include_router(driftsagent_router)


@app.get("/")
def root() -> dict:
    return {"service": "Driftsagent API", "versjon": "0.1.0", "status": "ok"}
