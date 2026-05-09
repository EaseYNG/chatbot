from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.config import CORS_ORIGINS, API_PREFIX


def create_app() -> FastAPI:
    app = FastAPI(title="LangChain Chatbot API", version="1.0.0")
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
