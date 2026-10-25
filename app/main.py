from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.generation import router as generation_router
from app.core.config import settings

app = FastAPI(
    title="Renewable Generation Intelligence API",
    version="1.0.0",
    description="A typed proxy and analysis layer over Elexon generation datasets.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(generation_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
