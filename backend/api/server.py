import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.config import CORS_ORIGINS, API_PREFIX

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="LangChain Chatbot API", version="1.0.0")
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {str(exc)}"},
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix=API_PREFIX)
    return app


app = create_app()
