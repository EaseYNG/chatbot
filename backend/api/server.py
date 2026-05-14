from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import CORS_ORIGINS, API_PREFIX
from backend.memory.database import init_db, close_db
from backend.memory.checkpointer import CheckpointerProvider

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield
    await close_db()
    try:
        CheckpointerProvider().close()
    except Exception as exc:
        logger.warning("Error closing checkpointer: %s", exc)


app = FastAPI(lifespan=lifespan, title="Multi-Agent Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.api.routes import router  # noqa: E402
from backend.auth import auth_router  # noqa: E402

app.include_router(router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", str(exc), exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
