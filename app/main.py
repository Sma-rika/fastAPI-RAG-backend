from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings
from app.core.dependencies import close_resources

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_resources()

app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)
app.include_router(router, prefix="/api/v1")

@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
